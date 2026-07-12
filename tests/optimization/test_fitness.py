"""Testes da função fitness e suas penalidades."""

from dataclasses import replace

import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization import RoutingFitness


def balanced_chromosome(problem: RoutingProblem) -> RouteChromosome:
    """Divide o cenário pequeno em duas rotas de carga 22."""
    return RouteChromosome.from_permutation(problem.delivery_ids, (4, 4))


def violation_codes(fitness: RoutingFitness, chromosome: RouteChromosome) -> set[str]:
    """Retorna somente os códigos para simplificar asserções."""
    return {item.code for item in fitness.evaluate(chromosome).violations}


def test_balanced_solution_is_feasible_and_detailed(
    small_problem: RoutingProblem,
) -> None:
    """Um plano dentro dos limites deve gerar somente custo objetivo."""
    evaluation = RoutingFitness(small_problem).evaluate(
        balanced_chromosome(small_problem)
    )

    assert evaluation.feasible
    assert evaluation.penalty_cost == 0
    assert evaluation.total_cost == evaluation.objective_cost
    assert evaluation.total_distance_km > 0
    assert evaluation.total_operating_cost > 0
    assert evaluation.vehicles_used == 2
    assert len(evaluation.routes) == 2
    assert all(route.capacity_excess == 0 for route in evaluation.routes)
    assert all(route.range_excess_km == 0 for route in evaluation.routes)


def test_capacity_excess_receives_dominant_penalty(
    small_problem: RoutingProblem,
) -> None:
    """Concentrar todas as entregas deve exceder o primeiro veículo."""
    chromosome = RouteChromosome.from_permutation(
        small_problem.delivery_ids,
        (len(small_problem.deliveries), 0),
    )
    evaluation = RoutingFitness(small_problem).evaluate(chromosome)

    assert not evaluation.feasible
    assert "capacity_exceeded" in violation_codes(
        RoutingFitness(small_problem), chromosome
    )
    assert evaluation.penalty_cost >= 90_000
    assert evaluation.routes[0].capacity_excess == pytest.approx(9)


def test_missing_and_unknown_deliveries_are_penalized(
    small_problem: RoutingProblem,
) -> None:
    """Cobertura diferente do cenário deve produzir diagnóstico explícito."""
    ids = (*small_problem.delivery_ids[:-1], "ENT-DESCONHECIDA")
    chromosome = RouteChromosome.from_permutation(ids, (4, 4))

    codes = violation_codes(RoutingFitness(small_problem), chromosome)

    assert {"missing_delivery", "unknown_delivery"} <= codes


def test_unavailable_vehicle_and_range_are_penalized(
    small_problem: RoutingProblem,
) -> None:
    """Uso de veículo indisponível e autonomia excedida são restrições duras."""
    first = replace(small_problem.vehicles[0], available=False, range_km=0.1)
    problem = replace(
        small_problem,
        vehicles=(first, small_problem.vehicles[1]),
    )
    chromosome = balanced_chromosome(problem)

    codes = violation_codes(RoutingFitness(problem), chromosome)

    assert {"unavailable_vehicle", "range_exceeded"} <= codes


def test_critical_delivery_is_favored_earlier(
    small_problem: RoutingProblem,
) -> None:
    """Com a mesma distância, atender a entrega crítica antes deve custar menos."""
    remaining = tuple(
        delivery_id
        for delivery_id in small_problem.delivery_ids
        if delivery_id not in {"ENT-001", "ENT-004"}
    )
    critical_first = RouteChromosome((("ENT-001", "ENT-004"), remaining))
    low_first = RouteChromosome((("ENT-004", "ENT-001"), remaining))
    fitness = RoutingFitness(small_problem)

    assert fitness(critical_first) < fitness(low_first)


def test_vehicle_count_mismatch_is_penalized(
    small_problem: RoutingProblem,
) -> None:
    """A quantidade de rotas deve corresponder à frota carregada."""
    chromosome = RouteChromosome((small_problem.delivery_ids,))

    assert "vehicle_count_mismatch" in violation_codes(
        RoutingFitness(small_problem), chromosome
    )
