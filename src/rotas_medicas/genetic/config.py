"""Configuração validada do algoritmo genético."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneticConfig:
    """Parâmetros de evolução para um problema de minimização."""

    population_size: int = 100
    max_generations: int = 500
    crossover_rate: float = 0.9
    mutation_rate: float = 0.2
    elite_count: int = 2
    tournament_size: int = 3
    stagnation_generations: int | None = 100
    target_cost: float | None = None
    improvement_tolerance: float = 1e-9
    seed: int | None = None

    def __post_init__(self) -> None:
        """Falha cedo quando uma configuração não pode ser executada."""
        if self.population_size < 2:
            raise ValueError("A população deve possuir ao menos dois indivíduos.")
        if self.max_generations < 1:
            raise ValueError("O número máximo de gerações deve ser positivo.")
        if not 0 <= self.crossover_rate <= 1:
            raise ValueError("A taxa de crossover deve estar entre zero e um.")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("A taxa de mutação deve estar entre zero e um.")
        if not 1 <= self.elite_count < self.population_size:
            raise ValueError("O elitismo deve ser menor que a população.")
        if not 2 <= self.tournament_size <= self.population_size:
            raise ValueError("O torneio deve conter entre dois e a população total.")
        if self.stagnation_generations is not None and self.stagnation_generations < 1:
            raise ValueError("O limite de estagnação deve ser positivo.")
        if self.improvement_tolerance < 0:
            raise ValueError("A tolerância de melhoria não pode ser negativa.")
