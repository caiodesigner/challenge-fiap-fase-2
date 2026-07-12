"""Entidades validadas do problema de roteamento médico."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class Priority(StrEnum):
    """Níveis de criticidade aceitos para uma entrega."""

    CRITICAL = "critica"
    HIGH = "alta"
    NORMAL = "normal"
    LOW = "baixa"


class DestinationType(StrEnum):
    """Tipos de ponto atendidos pelo sistema."""

    HEALTH_UNIT = "unidade_saude"
    HOME_CARE = "atendimento_domiciliar"


def _validate_coordinates(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("A latitude deve estar entre -90 e 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("A longitude deve estar entre -180 e 180.")


@dataclass(frozen=True, slots=True)
class Depot:
    """Ponto único de início e término das rotas."""

    id: str
    name: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not self.id or not self.name:
            raise ValueError("Depósito deve possuir identificador e nome.")
        _validate_coordinates(self.latitude, self.longitude)


@dataclass(frozen=True, slots=True)
class Delivery:
    """Demanda indivisível a ser atendida por um veículo."""

    id: str
    destination: str
    destination_type: DestinationType
    latitude: float
    longitude: float
    demand: float
    priority: Priority
    target_minutes: int | None
    cargo_description: str

    def __post_init__(self) -> None:
        if not self.id or not self.destination or not self.cargo_description:
            raise ValueError("Entrega deve possuir identificação e descrição.")
        _validate_coordinates(self.latitude, self.longitude)
        if self.demand <= 0:
            raise ValueError("A demanda deve ser positiva.")
        if self.target_minutes is not None and self.target_minutes <= 0:
            raise ValueError("O prazo-alvo deve ser positivo.")


@dataclass(frozen=True, slots=True)
class Vehicle:
    """Veículo e seus limites operacionais."""

    id: str
    description: str
    capacity: float
    range_km: float
    fixed_cost: float
    cost_per_km: float
    available: bool

    def __post_init__(self) -> None:
        if not self.id or not self.description:
            raise ValueError("Veículo deve possuir identificação e descrição.")
        if self.capacity <= 0 or self.range_km <= 0:
            raise ValueError("Capacidade e autonomia devem ser positivas.")
        if self.fixed_cost < 0 or self.cost_per_km < 0:
            raise ValueError("Custos do veículo não podem ser negativos.")


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    """Expectativas documentadas para um cenário de demonstração."""

    id: str
    name: str
    description: str
    planning_date: str
    seed: int
    expected_feasible: bool
    expected_infeasibility_reason: str | None


@dataclass(frozen=True, slots=True)
class RoutingProblem:
    """Instância completa e consistente de roteamento."""

    metadata: ScenarioMetadata
    depot: Depot
    vehicles: tuple[Vehicle, ...]
    deliveries: tuple[Delivery, ...]
    priority_weights: Mapping[Priority, int]

    def __post_init__(self) -> None:
        if not self.vehicles:
            raise ValueError("O problema deve possuir ao menos um veículo.")
        if not self.deliveries:
            raise ValueError("O problema deve possuir ao menos uma entrega.")
        vehicle_ids = [vehicle.id for vehicle in self.vehicles]
        delivery_ids = [delivery.id for delivery in self.deliveries]
        if len(vehicle_ids) != len(set(vehicle_ids)):
            raise ValueError("Identificadores de veículo devem ser únicos.")
        if len(delivery_ids) != len(set(delivery_ids)):
            raise ValueError("Identificadores de entrega devem ser únicos.")
        if set(self.priority_weights) != set(Priority):
            raise ValueError("Todas as prioridades devem possuir peso.")
        if any(weight <= 0 for weight in self.priority_weights.values()):
            raise ValueError("Pesos de prioridade devem ser positivos.")
        object.__setattr__(
            self,
            "priority_weights",
            MappingProxyType(dict(self.priority_weights)),
        )

    @property
    def delivery_ids(self) -> tuple[str, ...]:
        """Retorna os IDs na ordem de entrada do cenário."""
        return tuple(delivery.id for delivery in self.deliveries)

    @property
    def deliveries_by_id(self) -> Mapping[str, Delivery]:
        """Indexa entregas pelo identificador."""
        return MappingProxyType({delivery.id: delivery for delivery in self.deliveries})
