"""Integração do motor genético com a fitness de roteamento."""

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import GeneticAlgorithm, GeneticConfig
from rotas_medicas.optimization import RoutingFitness


def test_genetic_algorithm_finds_feasible_small_plan(
    small_problem: RoutingProblem,
) -> None:
    """O fluxo completo deve produzir um plano válido para o cenário pequeno."""
    fitness = RoutingFitness(small_problem)
    algorithm = GeneticAlgorithm(
        GeneticConfig(
            population_size=50,
            max_generations=80,
            crossover_rate=0.9,
            mutation_rate=0.35,
            elite_count=3,
            tournament_size=4,
            stagnation_generations=25,
            seed=small_problem.metadata.seed,
        )
    )

    result = algorithm.run(
        small_problem.delivery_ids,
        len(small_problem.vehicles),
        fitness,
    )
    evaluation = fitness.evaluate(result.best_chromosome)

    assert evaluation.feasible
    assert evaluation.penalty_cost == 0
    assert result.best_cost == evaluation.total_cost
    assert result.best_chromosome.contains_exactly(small_problem.delivery_ids)
