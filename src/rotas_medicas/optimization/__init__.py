"""Distâncias, restrições e função fitness de roteamento."""

from rotas_medicas.optimization.constraints import (
    FeasibilityIssue,
    find_feasibility_issues,
)
from rotas_medicas.optimization.distance import DistanceMatrix, haversine_km
from rotas_medicas.optimization.fitness import (
    ConstraintViolation,
    FitnessConfig,
    FitnessEvaluation,
    FitnessWeights,
    RouteMetrics,
    RoutingFitness,
)

__all__ = [
    "ConstraintViolation",
    "DistanceMatrix",
    "FeasibilityIssue",
    "FitnessConfig",
    "FitnessEvaluation",
    "FitnessWeights",
    "RouteMetrics",
    "RoutingFitness",
    "find_feasibility_issues",
    "haversine_km",
]
