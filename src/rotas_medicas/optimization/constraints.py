"""Diagnóstico prévio de inviabilidade de uma instância."""

from __future__ import annotations

from dataclasses import dataclass

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.optimization.distance import DistanceMatrix


@dataclass(frozen=True, slots=True)
class FeasibilityIssue:
    """Causa necessária de inviabilidade detectada antes da otimização."""

    code: str
    message: str
    delivery_id: str | None = None


def find_feasibility_issues(
    problem: RoutingProblem,
    distances: DistanceMatrix | None = None,
) -> tuple[FeasibilityIssue, ...]:
    """Detecta condições que tornam impossível produzir um plano executável."""
    available = tuple(vehicle for vehicle in problem.vehicles if vehicle.available)
    if not available:
        return (
            FeasibilityIssue(
                "no_available_vehicle",
                "Não existe veículo disponível para realizar as entregas.",
            ),
        )

    issues: list[FeasibilityIssue] = []
    maximum_capacity = max(vehicle.capacity for vehicle in available)
    total_capacity = sum(vehicle.capacity for vehicle in available)
    total_demand = sum(delivery.demand for delivery in problem.deliveries)
    if total_demand > total_capacity:
        issues.append(
            FeasibilityIssue(
                "insufficient_total_capacity",
                "A demanda total excede a capacidade agregada da frota disponível.",
            )
        )

    matrix = distances or DistanceMatrix.from_problem(problem)
    maximum_range = max(vehicle.range_km for vehicle in available)
    for delivery in problem.deliveries:
        if delivery.demand > maximum_capacity:
            issues.append(
                FeasibilityIssue(
                    "delivery_exceeds_vehicle_capacity",
                    (
                        f"A entrega {delivery.id} excede a capacidade "
                        "de todos os veículos."
                    ),
                    delivery.id,
                )
            )
        minimum_round_trip = 2 * matrix.between(problem.depot.id, delivery.id)
        if minimum_round_trip > maximum_range:
            issues.append(
                FeasibilityIssue(
                    "delivery_out_of_range",
                    f"A entrega {delivery.id} está fora da autonomia de toda a frota.",
                    delivery.id,
                )
            )
    return tuple(issues)
