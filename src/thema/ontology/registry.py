"""The builder registry: method name to implementation.

One place maps a `--method` string to a class, so the CLI, the demo loader and the evaluation all
agree on what names exist and none of them carries its own list.
"""

from thema.ontology.base import OntologyBuilder
from thema.ontology.recurrent import RecurrentDag
from thema.ontology.ward import WardTree

#: Every shipped method. `recurrent_dag` is registered so it can be built and evaluated; the demo
#: stays on `ward_tree` until it passes the spec's §14 go/no-go.
BUILDERS: dict[str, type[OntologyBuilder]] = {
    WardTree.method: WardTree,
    RecurrentDag.method: RecurrentDag,
}


def builder(method: str) -> OntologyBuilder:
    """Instantiate a builder by method name.

    Args:
        method: The method id.

    Returns:
        A fresh builder.

    Raises:
        KeyError: If the name is unknown, listing the ones that are not.
    """
    if method not in BUILDERS:
        raise KeyError(f"unknown method {method!r}; known: {', '.join(sorted(BUILDERS))}")
    return BUILDERS[method]()
