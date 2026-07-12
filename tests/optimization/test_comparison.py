import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.optimization import (
    RoutingFitness,
    compare_with_best_baseline,
    original_order,
)


def test_comparison_uses_best_feasible_baseline(
    small_problem: RoutingProblem,
) -> None:
    optimized = RoutingFitness(small_problem).evaluate(original_order(small_problem))

    comparison = compare_with_best_baseline(small_problem, optimized)

    assert comparison.baseline_name
    assert comparison.baseline_distance_km > 0
    assert comparison.baseline_operating_cost > 0
    assert comparison.baseline_estimated_minutes > 0
    assert comparison.optimized_vehicles > 0


def test_comparison_reports_signed_savings(small_problem: RoutingProblem) -> None:
    optimized = RoutingFitness(small_problem).evaluate(original_order(small_problem))

    comparison = compare_with_best_baseline(small_problem, optimized)

    expected = comparison.baseline_distance_km - comparison.optimized_distance_km
    assert comparison.distance_savings_km == pytest.approx(expected, abs=1e-4)
    assert comparison.time_savings_minutes == pytest.approx(
        comparison.distance_savings_km / 30 * 60,
        abs=0.02,
    )
