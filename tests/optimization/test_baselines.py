"""Testes das heurísticas usadas como referência."""

import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization import BASELINES, RoutingFitness


@pytest.mark.parametrize("name", sorted(BASELINES))
def test_baseline_is_deterministic_and_preserves_deliveries(
    name: str,
    small_problem: RoutingProblem,
) -> None:
    """Toda referência deve produzir a mesma solução completa a cada chamada."""
    baseline = BASELINES[name]
    first = baseline(small_problem)
    second = baseline(small_problem)

    assert first == second
    assert first.contains_exactly(small_problem.delivery_ids)
    assert first.vehicle_count == len(small_problem.vehicles)


@pytest.mark.parametrize("name", sorted(BASELINES))
def test_baseline_produces_feasible_small_plan(
    name: str,
    small_problem: RoutingProblem,
) -> None:
    """As referências devem respeitar limites no cenário pequeno."""
    chromosome = BASELINES[name](small_problem)

    assert RoutingFitness(small_problem).evaluate(chromosome).feasible


def test_baselines_are_independent_solutions(
    small_problem: RoutingProblem,
) -> None:
    """As estratégias devem explorar pelo menos duas ordenações distintas."""
    chromosomes: set[RouteChromosome] = {
        baseline(small_problem) for baseline in BASELINES.values()
    }

    assert len(chromosomes) >= 2
