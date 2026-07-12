"""Testes do ciclo de evolução do algoritmo genético."""

import math
from itertools import pairwise

import pytest

from rotas_medicas.genetic import GeneticAlgorithm, GeneticConfig, RouteChromosome

DELIVERIES = tuple(f"E{index}" for index in range(8))
EXPECTED_POSITIONS = {
    delivery_id: index for index, delivery_id in enumerate(DELIVERIES)
}


def sequence_cost(chromosome: RouteChromosome) -> float:
    """Penaliza distância da ordem conhecida e desequilíbrio entre rotas."""
    order_cost = sum(
        abs(index - EXPECTED_POSITIONS[delivery_id])
        for index, delivery_id in enumerate(chromosome.delivery_ids)
    )
    imbalance = max(chromosome.route_sizes) - min(chromosome.route_sizes)
    return float(order_cost + imbalance)


def test_algorithm_is_reproducible_and_preserves_deliveries() -> None:
    """Execuções com a mesma seed devem produzir o mesmo resultado."""
    config = GeneticConfig(
        population_size=30,
        max_generations=80,
        crossover_rate=0.9,
        mutation_rate=0.35,
        elite_count=2,
        tournament_size=3,
        stagnation_generations=30,
        target_cost=0,
        seed=2026,
    )

    first = GeneticAlgorithm(config).run(DELIVERIES, 2, sequence_cost)
    second = GeneticAlgorithm(config).run(DELIVERIES, 2, sequence_cost)

    assert first == second
    assert first.best_chromosome.contains_exactly(DELIVERIES)
    assert first.best_cost == 0
    assert first.stop_reason == "target_cost"
    assert len(first.history) == first.generations_executed + 1


def test_elitism_keeps_best_generation_cost_monotonic() -> None:
    """O melhor custo não pode piorar entre gerações com elitismo."""
    config = GeneticConfig(
        population_size=20,
        max_generations=15,
        elite_count=2,
        stagnation_generations=None,
        seed=99,
    )
    result = GeneticAlgorithm(config).run(DELIVERIES, 3, sequence_cost)
    best_costs = [stats.best_cost for stats in result.history]

    assert result.stop_reason == "max_generations"
    assert result.generations_executed == 15
    assert all(current <= previous for previous, current in pairwise(best_costs))


def test_stops_after_configured_stagnation() -> None:
    """Sem qualquer melhoria, a execução deve parar pelo limite configurado."""
    config = GeneticConfig(
        population_size=10,
        max_generations=50,
        elite_count=1,
        tournament_size=2,
        stagnation_generations=4,
        seed=5,
    )
    result = GeneticAlgorithm(config).run(DELIVERIES, 2, lambda _: 10.0)

    assert result.stop_reason == "stagnation"
    assert result.generations_executed == 4


def test_rejects_non_finite_cost() -> None:
    """NaN e infinitos não podem participar da ordenação da população."""
    config = GeneticConfig(population_size=4, max_generations=2, elite_count=1)

    with pytest.raises(ValueError, match="número finito"):
        GeneticAlgorithm(config).run(("A", "B"), 1, lambda _: math.inf)


@pytest.mark.parametrize(
    "overrides",
    [
        {"population_size": 1},
        {"max_generations": 0},
        {"crossover_rate": 1.1},
        {"mutation_rate": -0.1},
        {"elite_count": 10},
        {"tournament_size": 1},
        {"stagnation_generations": 0},
    ],
)
def test_rejects_invalid_configuration(overrides: dict[str, object]) -> None:
    """Parâmetros incoerentes devem falhar na criação da configuração."""
    parameters: dict[str, object] = {"population_size": 10}
    parameters.update(overrides)
    with pytest.raises(ValueError, match=r"."):
        GeneticConfig(**parameters)  # type: ignore[arg-type]
