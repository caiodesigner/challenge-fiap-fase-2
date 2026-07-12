"""Motor de evolução para minimizar custos de cromossomos multirrota."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from statistics import fmean

from rotas_medicas.genetic.chromosome import RouteChromosome
from rotas_medicas.genetic.config import GeneticConfig
from rotas_medicas.genetic.operators import mutate, order_crossover
from rotas_medicas.genetic.population import create_initial_population

CostFunction = Callable[[RouteChromosome], float]


@dataclass(frozen=True, slots=True)
class EvaluatedIndividual:
    """Cromossomo associado ao custo calculado para ele."""

    chromosome: RouteChromosome
    cost: float


@dataclass(frozen=True, slots=True)
class GenerationStats:
    """Resumo de uma geração, incluindo a população inicial (geração zero)."""

    generation: int
    best_cost: float
    average_cost: float
    worst_cost: float


@dataclass(frozen=True, slots=True)
class GeneticResult:
    """Melhor solução encontrada e histórico completo da execução."""

    best_chromosome: RouteChromosome
    best_cost: float
    generations_executed: int
    stop_reason: str
    history: tuple[GenerationStats, ...]


class GeneticAlgorithm:
    """Executa seleção, crossover, mutação e elitismo para minimização."""

    def __init__(self, config: GeneticConfig) -> None:
        self._config = config

    def run(
        self,
        delivery_ids: Sequence[str],
        vehicle_count: int,
        cost_function: CostFunction,
    ) -> GeneticResult:
        """Evolui uma população até um dos critérios de parada."""
        rng = random.Random(self._config.seed)
        population = create_initial_population(
            delivery_ids,
            vehicle_count,
            self._config.population_size,
            rng,
        )
        evaluated = self._evaluate(population, cost_function)
        best = evaluated[0]
        history = [self._stats(0, evaluated)]
        stagnant_generations = 0

        if self._target_reached(best.cost):
            return self._result(best, 0, "target_cost", history)

        for generation in range(1, self._config.max_generations + 1):
            population = self._next_population(evaluated, rng)
            evaluated = self._evaluate(population, cost_function)
            generation_best = evaluated[0]
            history.append(self._stats(generation, evaluated))

            improvement = best.cost - generation_best.cost
            if improvement > self._config.improvement_tolerance:
                best = generation_best
                stagnant_generations = 0
            else:
                stagnant_generations += 1

            if self._target_reached(best.cost):
                return self._result(best, generation, "target_cost", history)
            if self._stagnated(stagnant_generations):
                return self._result(best, generation, "stagnation", history)

        return self._result(
            best,
            self._config.max_generations,
            "max_generations",
            history,
        )

    def _evaluate(
        self,
        population: Sequence[RouteChromosome],
        cost_function: CostFunction,
    ) -> list[EvaluatedIndividual]:
        evaluated = []
        for chromosome in population:
            cost = float(cost_function(chromosome))
            if not math.isfinite(cost):
                raise ValueError("A função de custo deve retornar um número finito.")
            evaluated.append(EvaluatedIndividual(chromosome, cost))
        return sorted(evaluated, key=lambda individual: individual.cost)

    def _next_population(
        self,
        evaluated: Sequence[EvaluatedIndividual],
        rng: random.Random,
    ) -> list[RouteChromosome]:
        population = [
            individual.chromosome
            for individual in evaluated[: self._config.elite_count]
        ]
        while len(population) < self._config.population_size:
            first_parent = self._tournament(evaluated, rng).chromosome
            second_parent = self._tournament(evaluated, rng).chromosome
            if rng.random() < self._config.crossover_rate:
                children = order_crossover(first_parent, second_parent, rng)
            else:
                children = (first_parent, second_parent)

            for child in children:
                if rng.random() < self._config.mutation_rate:
                    child = mutate(child, rng)
                population.append(child)
                if len(population) == self._config.population_size:
                    break
        return population

    def _tournament(
        self,
        evaluated: Sequence[EvaluatedIndividual],
        rng: random.Random,
    ) -> EvaluatedIndividual:
        competitors = rng.sample(list(evaluated), self._config.tournament_size)
        return min(competitors, key=lambda individual: individual.cost)

    def _target_reached(self, cost: float) -> bool:
        target = self._config.target_cost
        return target is not None and cost <= target

    def _stagnated(self, stagnant_generations: int) -> bool:
        limit = self._config.stagnation_generations
        return limit is not None and stagnant_generations >= limit

    @staticmethod
    def _stats(
        generation: int,
        evaluated: Sequence[EvaluatedIndividual],
    ) -> GenerationStats:
        costs = [individual.cost for individual in evaluated]
        return GenerationStats(generation, min(costs), fmean(costs), max(costs))

    @staticmethod
    def _result(
        best: EvaluatedIndividual,
        generations_executed: int,
        stop_reason: str,
        history: Sequence[GenerationStats],
    ) -> GeneticResult:
        return GeneticResult(
            best.chromosome,
            best.cost,
            generations_executed,
            stop_reason,
            tuple(history),
        )
