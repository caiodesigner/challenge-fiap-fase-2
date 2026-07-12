"""Entidades e carregamento do domínio de roteamento."""

from rotas_medicas.domain.models import (
    Delivery,
    Depot,
    DestinationType,
    Priority,
    RoutingProblem,
    ScenarioMetadata,
    Vehicle,
)
from rotas_medicas.domain.scenario import load_scenario

__all__ = [
    "Delivery",
    "Depot",
    "DestinationType",
    "Priority",
    "RoutingProblem",
    "ScenarioMetadata",
    "Vehicle",
    "load_scenario",
]
