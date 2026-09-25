"""The validation statistics, on cases whose answers are obvious by inspection."""


from thema.validation import best_match, seed_stability, shape


def test_shape_of_a_known_little_tree() -> None:
    parents = {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]}
    sizes = {"a": 10, "b": 6, "c": 5, "d": 3}
    got = shape(parents, sizes)
    assert got["nodes"] == 4
    assert got["roots"] == 1 and got["root_fraction"] == 0.25
    assert got["max_depth"] == 2 and got["median_depth"] == 1.0
    assert got["multi_parent_fraction"] == 0.25, "only d has two parents"
    # a has 2 children, b and c have 1 each -> [2, 1, 1], median 1
    assert got["median_branching"] == 1.0
    assert got["size_median"] == 5.5


def test_a_forest_of_singletons_is_all_roots_at_depth_zero() -> None:
    parents = {str(i): [] for i in range(5)}
    got = shape(parents, {str(i): 3 for i in range(5)})
    assert got["root_fraction"] == 1.0 and got["max_depth"] == 0


def test_best_match_finds_the_most_similar_set() -> None:
    left = [frozenset("abc"), frozenset("xyz")]
    right = [frozenset("xy"), frozenset("abcd")]
    matched, scores = best_match(left, right)
    assert matched == [1, 0]
    assert scores[0] == 3 / 4 and scores[1] == 2 / 3


def test_best_match_returns_minus_one_against_nothing() -> None:
    matched, scores = best_match([frozenset("ab")], [])
    assert matched == [-1] and scores == [0.0]


def test_seed_stability_of_an_identical_rebuild_is_perfect() -> None:
    sets = [frozenset("abc"), frozenset("defg")]
    got = seed_stability(sets, list(sets))
    assert got["mean_jaccard"] == 1.0
    assert got["matched_at_0.9"] == 1.0
    assert got["member_agreement"] == 1.0


def test_seed_stability_of_a_disjoint_rebuild_is_zero() -> None:
    got = seed_stability([frozenset("abc")], [frozenset("xyz")])
    assert got["mean_jaccard"] == 0.0
    assert got["matched_at_0.5"] == 0.0


def test_seed_stability_reports_both_directions() -> None:
    """A build that splits one theme in two scores differently each way, and both are reported."""
    first = [frozenset("abcdef")]
    second = [frozenset("abc"), frozenset("def")]
    got = seed_stability(first, second)
    assert got["themes_first"] == 1 and got["themes_second"] == 2
    assert got["mean_jaccard"] == 0.5
    assert got["mean_jaccard_reverse"] == 0.5
