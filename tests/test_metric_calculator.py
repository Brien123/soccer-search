from stats.metric_calculator import MetricCalculator


def test_precision_counts_top_k() -> None:
    metrics = MetricCalculator()
    flags = [True, False, True, False, True]
    assert metrics.precision(flags, 5) == 0.6
    assert metrics.precision(flags, 2) == 0.5


def test_recall_uses_relevant_total() -> None:
    metrics = MetricCalculator()
    flags = [True, False, True, False, True]
    assert metrics.recall(flags, 10, 5) == 0.3


def test_f1_is_harmonic_mean() -> None:
    metrics = MetricCalculator()
    assert metrics.f1(0.6, 0.3) == 0.4
    assert metrics.f1(0.0, 0.0) == 0.0


def test_counts_breakdown() -> None:
    metrics = MetricCalculator()
    tp, fp, fn = metrics.counts([True, False, True], 4, 3)
    assert (tp, fp, fn) == (2, 1, 2)


def test_reciprocal_rank_first_relevant() -> None:
    metrics = MetricCalculator()
    assert metrics.reciprocal_rank([False, False, True]) == 1 / 3
    assert metrics.reciprocal_rank([False, False, False]) == 0.0


def test_ndcg_perfect_ranking_is_one() -> None:
    metrics = MetricCalculator()
    assert metrics.ndcg([True, True, False], 2, 3) == 1.0


def test_ndcg_zero_when_no_relevant_total() -> None:
    metrics = MetricCalculator()
    assert metrics.ndcg([True, False], 0, 2) == 0.0


def test_empty_flags_return_zero() -> None:
    metrics = MetricCalculator()
    assert metrics.precision([], 5) == 0.0
    assert metrics.recall([], 5, 5) == 0.0
