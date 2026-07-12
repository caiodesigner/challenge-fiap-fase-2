"""Distâncias, restrições e função fitness de roteamento."""

from rotas_medicas.optimization.baselines import (
    BASELINES,
    nearest_neighbor,
    original_order,
    priority_distance,
)
from rotas_medicas.optimization.comparison import (
    BaselineComparison,
    compare_with_best_baseline,
)
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
    "BASELINES",
    "BaselineComparison",
    "ConstraintViolation",
    "DistanceMatrix",
    "FeasibilityIssue",
    "FitnessConfig",
    "FitnessEvaluation",
    "FitnessWeights",
    "RouteMetrics",
    "RoutingFitness",
    "compare_with_best_baseline",
    "find_feasibility_issues",
    "haversine_km",
    "nearest_neighbor",
    "original_order",
    "priority_distance",
]
