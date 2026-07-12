"""Representação, operadores e motor do algoritmo genético."""

from rotas_medicas.genetic.chromosome import RouteChromosome
from rotas_medicas.genetic.config import GeneticConfig
from rotas_medicas.genetic.engine import (
    GenerationStats,
    GeneticAlgorithm,
    GeneticResult,
)

__all__ = [
    "GenerationStats",
    "GeneticAlgorithm",
    "GeneticConfig",
    "GeneticResult",
    "RouteChromosome",
]
