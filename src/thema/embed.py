"""Turn descriptions into vectors, and put them on the unit sphere before anything clusters them.

This is the only module that imports ``sentence_transformers`` or torch, the same containment
``llm.py`` gives the Anthropic SDK and for the same reason: the arithmetic in ``cluster.py`` must
stay testable without a multi-gigabyte install or a model download. ``tests/test_embed.py`` checks
that containment by walking the sources, so it is machine-checked rather than a convention.

Model choice is D7 in ``docs/brief.md``: BioLORD-2023, whose training objective makes embedding
geometry mirror ontology structure, which is exactly this task. Qwen3-Embedding-0.6B is the named
comparison arm and is not built here.

The normalization is not a detail. For unit vectors ||a - b||^2 = 2 - 2*cos(a, b), so Euclidean
distance becomes a monotone function of cosine similarity, and Ward's variance criterion -- which
is defined on Euclidean distance and on nothing else -- becomes legitimate. Without it the distance
partly reflects vector magnitude, and magnitude tracks text length, so the tree would encode how
long a description is alongside what it says. That is the silent bug the 2024 prototype shipped
with, and it is silent precisely because the output still looks like a tree.
"""

from collections.abc import Sequence

import numpy as np

#: BioLORD-2023. Pinned by revision as well as by name, because an unpinned model is an unpinned
#: input and this project pins every other one.
BIOLORD_MODEL = "FremyCompany/BioLORD-2023"

#: The revision to fetch. Set to a commit sha to freeze the weights; ``main`` is a floating
#: reference and is recorded as such in the ontology summary so a run is never silently unpinned.
BIOLORD_REVISION = "main"

#: The comparison arm named in docs/brief.md D7. A strong general-purpose embedder with no
#: biomedical training, so agreement between the two trees is evidence the structure is in the
#: biology rather than in one encoder's idiosyncrasy.
QWEN_MODEL = "Qwen/Qwen3-Embedding-0.6B"
QWEN_REVISION = "main"

#: WRONG, AND LEFT HERE AS THE RECORD OF HOW: this said BioLORD had "a 512-token window" so
#: "nothing truncates". The architecture does carry 514 positions, but the shipped
#: sentence-transformers config caps ``max_seq_length`` at **128**, and that cap is what runs. The
#: median description is 231 tokens and ALL 1,850 exceeded it, so ~45% of every description was
#: silently discarded before it was ever embedded, for every build and for E. The claim was made
#: from the architecture without measuring the loaded object.
#: See docs/status/2026-09-24-embedding-truncation.md and DECISIONS.md, 24 Sep 2026.
BIOLORD_EFFECTIVE_MAX_TOKENS = 128

#: MedCPT's window, and it is enforced here rather than assumed. Checked against the corpus.
MODEL_MAX_TOKENS = 512

#: The encoder in use. MedCPT's article encoder is trained on PubMed title+abstract pairs -- whole
#: paragraphs of literature prose, which is what a generated description is -- against 255M user
#: click pairs. BioLORD-2023 is a concept/definition embedder: it aligns short names and
#: definitions to an ontology, a different input shape from a 135-word paragraph, and it was chosen
#: for that ontology-mirroring objective without checking the window it actually reads.
#:
#: Chosen on published evidence rather than an in-project benchmark: a Nature Communications 2026
#: comparison of embedders on gene-set / GO-BP functional descriptions places this encoder in the
#: top tier alongside OpenAI-TE3 and Gemini when fed free text, with pubmedbert-base-embeddings
#: below it. OpenAI-TE3 scored higher and was refused: a frozen ontology needs an embedder that can
#: be PINNED, and an API model behind a moving endpoint cannot be. See DECISIONS.md, 24 Sep 2026.
MEDCPT_MODEL = "ncbi/MedCPT-Article-Encoder"

#: Pinned to a commit, not to ``main``. BioLORD is recorded in every earlier manifest as ``main``,
#: a floating reference, so those artifacts cannot be reproduced from their manifests alone. This
#: one can.
MEDCPT_REVISION = "d05a736da4bb84ee4057b7f7999485be6ed85465"

#: MedCPT pools the CLS token, not the token mean. This is the model's own specification, not a
#: choice: its contrastive training put the sentence representation there.
MEDCPT_POOLING = "cls"

#: How many descriptions go to the encoder at once.
BATCH_SIZE = 64


def load_medcpt(
    model: str = MEDCPT_MODEL, revision: str = MEDCPT_REVISION
) -> tuple[object, object]:
    """Load the MedCPT article encoder and its tokenizer, on CPU.

    Args:
        model: The model id.
        revision: The revision to pin to.

    Returns:
        ``(tokenizer, model)``, the model in eval mode on CPU.
    """
    import torch
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model, revision=revision)
    encoder = AutoModel.from_pretrained(model, revision=revision)
    encoder.eval()
    encoder.to(torch.device("cpu"))
    return tokenizer, encoder


def medcpt_token_counts(texts: Sequence[str]) -> list[int]:
    """Token length of each text under MedCPT's tokenizer, untruncated.

    Exists so the window can be CHECKED rather than asserted. The previous encoder's window was
    stated from its architecture and never measured, and every description silently lost ~45% of
    itself for months.

    Args:
        texts: The descriptions.

    Returns:
        One token count per text, special tokens included.
    """
    tokenizer, _ = load_medcpt()
    return [len(tokenizer.encode(t, truncation=False)) for t in texts]


def embed_medcpt(
    texts: Sequence[str],
    model: str = MEDCPT_MODEL,
    revision: str = MEDCPT_REVISION,
    batch_size: int = BATCH_SIZE,
    max_length: int = MODEL_MAX_TOKENS,
) -> np.ndarray:
    """Embed descriptions with MedCPT's article encoder, CLS-pooled, then unit-normalize.

    The description text is the whole input: no pathway name, no title field, nothing prepended.
    Prepending the name was measured and rejected on 23 Sep -- it groups templates rather than
    biology -- and the same rule holds here.

    Args:
        texts: The descriptions, in the order their pathways will be reported in.
        model: The model id.
        revision: The revision.
        batch_size: How many to encode at once.
        max_length: Token window. Truncation at this length would be silent, so callers must check
            :func:`medcpt_token_counts` first; this function does not warn.

    Returns:
        A ``(len(texts), 768)`` float32 array of unit vectors.

    Raises:
        ValueError: If there is nothing to embed.
    """
    if not texts:
        raise ValueError("nothing to embed")
    import torch

    tokenizer, encoder = load_medcpt(model, revision)
    out: list[np.ndarray] = []
    with torch.no_grad():
        for begin in range(0, len(texts), batch_size):
            block = list(texts[begin : begin + batch_size])
            encoded = tokenizer(
                block, truncation=True, padding=True, return_tensors="pt", max_length=max_length
            )
            # CLS pooling, as MedCPT specifies: the representation is the first token.
            hidden = encoder(**encoded).last_hidden_state[:, 0, :]
            out.append(hidden.numpy())
    return l2_normalize(np.vstack(out).astype(np.float32))


def load_model(model: str = BIOLORD_MODEL, revision: str = BIOLORD_REVISION) -> object:
    """Load the sentence-transformer, downloading it on first use.

    Args:
        model: The model id.
        revision: The revision to pin to.

    Returns:
        The loaded model.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model, revision=revision)


def embed(
    texts: Sequence[str],
    model: str = BIOLORD_MODEL,
    revision: str = BIOLORD_REVISION,
    batch_size: int = BATCH_SIZE,
) -> np.ndarray:
    """Embed descriptions, then put them on the unit sphere.

    Normalization happens here rather than being left to the caller, so there is no code path in
    which an unnormalized matrix reaches a linkage. See the module docstring for why that matters.

    Args:
        texts: The descriptions, in the order their pathways will be reported in.
        model: The model id.
        revision: The revision.
        batch_size: How many to encode at once.

    Returns:
        A ``(len(texts), dim)`` float32 array of unit vectors.

    Raises:
        ValueError: If there is nothing to embed.
    """
    if not texts:
        raise ValueError("nothing to embed")
    encoder = load_model(model, revision)
    vectors = encoder.encode(
        list(texts), batch_size=batch_size, convert_to_numpy=True, show_progress_bar=True
    )
    return l2_normalize(np.asarray(vectors, dtype=np.float32))


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Scale every row to unit length.

    Args:
        vectors: A ``(n, dim)`` array.

    Returns:
        The same array with every row scaled to length 1. A zero row is left alone rather than
        producing a division by zero: it cannot be normalized, and turning it into NaN would
        poison every distance it takes part in instead of just its own.
    """
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.asarray(vectors / np.where(lengths == 0, 1.0, lengths), dtype=np.float32)
