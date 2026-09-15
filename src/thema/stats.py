"""Paired statistics for comparing two prompts on the same pathways.

The arms are not independent samples: every arm describes the SAME pathway, so a pathway that is
intrinsically hard is hard for all of them. An unpaired test would throw that structure away and
answer a question nobody asked -- whether two sets of 100 different pathways differ. McNemar's test
uses only the pathways where the arms DISAGREE, which is the evidence that actually distinguishes
them, and the discordant counts are reported beside the p-value because they are what a reader needs
to judge whether the result rests on anything.

The exact binomial form is used rather than the chi-square approximation. With discordant counts in
the teens the approximation is unreliable in exactly the range these experiments produce.
"""

from dataclasses import dataclass
from math import sqrt

from scipy.stats import binomtest, norm


@dataclass(frozen=True, slots=True)
class Paired:
    """The result of comparing two arms over the same pathways.

    Attributes:
        n: How many pathways were compared.
        both: Pathways where both arms carried the outcome.
        neither: Pathways where neither did.
        only_first: Pathways where only the first arm did -- a discordant pair.
        only_second: Pathways where only the second did -- the other discordant pair.
        rate_first: The first arm's rate.
        rate_second: The second arm's rate.
        difference: ``rate_first - rate_second``.
        low: Lower bound of the confidence interval on that difference.
        high: Upper bound.
        p_value: Two-sided exact McNemar p-value.
    """

    n: int
    both: int
    neither: int
    only_first: int
    only_second: int
    rate_first: float
    rate_second: float
    difference: float
    low: float
    high: float
    p_value: float

    @property
    def discordant(self) -> int:
        """How many pathways the two arms disagreed on -- all the evidence the test uses."""
        return self.only_first + self.only_second

    @property
    def significant(self) -> bool:
        """Whether the interval excludes no difference at the conventional level."""
        return self.p_value < 0.05


def mcnemar(first: dict[str, bool], second: dict[str, bool], confidence: float = 0.95) -> Paired:
    """Compare two arms over the pathways they share.

    Args:
        first: Outcome per pathway for one arm, typically "carries at least one wrong claim".
        second: The same for the other arm.
        confidence: Coverage for the interval on the difference in rates.

    Returns:
        The paired comparison.

    Raises:
        ValueError: If the two arms share no pathways. An empty comparison has no answer, and
            returning zeros would let a caller report "no difference" from no data.
    """
    shared = sorted(set(first) & set(second))
    if not shared:
        raise ValueError("the two arms share no pathways, so there is nothing to pair")

    both = sum(1 for k in shared if first[k] and second[k])
    neither = sum(1 for k in shared if not first[k] and not second[k])
    only_first = sum(1 for k in shared if first[k] and not second[k])
    only_second = sum(1 for k in shared if not first[k] and second[k])
    n = len(shared)

    discordant = only_first + only_second
    # With no discordant pairs the arms agreed on every pathway: there is no evidence of a
    # difference in either direction, which is p = 1 rather than a missing answer.
    p_value = (
        1.0
        if discordant == 0
        else binomtest(only_first, discordant, 0.5, alternative="two-sided").pvalue
    )

    difference = (only_first - only_second) / n
    # Wald interval for the difference between paired proportions: the variance depends only on the
    # discordant cells, which is the same reason the test does.
    variance = (discordant - (only_first - only_second) ** 2 / n) / n**2
    margin = norm.ppf(0.5 + confidence / 2) * sqrt(max(variance, 0.0))
    return Paired(
        n=n,
        both=both,
        neither=neither,
        only_first=only_first,
        only_second=only_second,
        rate_first=sum(1 for k in shared if first[k]) / n,
        rate_second=sum(1 for k in shared if second[k]) / n,
        difference=difference,
        low=difference - margin,
        high=difference + margin,
        p_value=p_value,
    )


def describe(result: Paired, first: str, second: str) -> list[str]:
    """Render a paired comparison as lines a report can print.

    Args:
        result: What :func:`mcnemar` computed.
        first: Name of the first arm.
        second: Name of the second arm.

    Returns:
        The lines, discordant counts before the p-value because they are what carries the result.
    """
    verdict = (
        "significant at the conventional level"
        if result.significant
        else "NOT established at this sample size"
    )
    return [
        f"  {first} {result.rate_first:.0%} vs {second} {result.rate_second:.0%}  "
        f"(n={result.n} paired pathways)",
        f"  discordant pairs: {result.only_first} only-{first}, "
        f"{result.only_second} only-{second}  ({result.discordant} total -- the whole evidence)",
        f"  concordant: {result.both} both, {result.neither} neither",
        f"  difference {result.difference:+.0%}  95% CI [{result.low:+.0%}, {result.high:+.0%}]",
        f"  exact McNemar p = {result.p_value:.3f}  -- {verdict}",
    ]
