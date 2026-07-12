"""Cálculo determinístico de distâncias geográficas."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations
from types import MappingProxyType

from rotas_medicas.domain import RoutingProblem

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    """Calcula a distância de grande círculo entre duas coordenadas."""
    first_latitude_rad = math.radians(first_latitude)
    second_latitude_rad = math.radians(second_latitude)
    latitude_delta = math.radians(second_latitude - first_latitude)
    longitude_delta = math.radians(second_longitude - first_longitude)
    haversine = math.sin(latitude_delta / 2) ** 2 + (
        math.cos(first_latitude_rad)
        * math.cos(second_latitude_rad)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(haversine))


@dataclass(frozen=True, slots=True)
class DistanceMatrix:
    """Matriz simétrica indexada por IDs do depósito e das entregas."""

    distances: Mapping[tuple[str, str], float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "distances", MappingProxyType(dict(self.distances)))

    def between(self, first_id: str, second_id: str) -> float:
        """Retorna zero para o mesmo ponto e falha para IDs desconhecidos."""
        if first_id == second_id:
            return 0.0
        try:
            return self.distances[(first_id, second_id)]
        except KeyError as error:
            raise KeyError(
                f"Distância não disponível entre {first_id!r} e {second_id!r}."
            ) from error

    @classmethod
    def from_problem(cls, problem: RoutingProblem) -> DistanceMatrix:
        """Pré-calcula todas as combinações de pontos do cenário."""
        coordinates = {
            problem.depot.id: (problem.depot.latitude, problem.depot.longitude),
            **{
                delivery.id: (delivery.latitude, delivery.longitude)
                for delivery in problem.deliveries
            },
        }
        distances: dict[tuple[str, str], float] = {}
        for first_id, second_id in combinations(coordinates, 2):
            first = coordinates[first_id]
            second = coordinates[second_id]
            distance = haversine_km(first[0], first[1], second[0], second[1])
            distances[(first_id, second_id)] = distance
            distances[(second_id, first_id)] = distance
        return cls(distances)
