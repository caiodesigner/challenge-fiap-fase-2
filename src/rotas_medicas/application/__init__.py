"""Casos de uso e orquestração da aplicação."""

from rotas_medicas.application.service import (
    InfeasibleScenarioError,
    InMemorySolutionStore,
    OptimizationFailedError,
    RouteApplicationService,
    ScenarioNotFoundError,
    ScenarioSummary,
    SolutionNotFoundError,
    SolutionRecord,
)

__all__ = [
    "InMemorySolutionStore",
    "InfeasibleScenarioError",
    "OptimizationFailedError",
    "RouteApplicationService",
    "ScenarioNotFoundError",
    "ScenarioSummary",
    "SolutionNotFoundError",
    "SolutionRecord",
]
