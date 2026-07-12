"""Avaliação determinística de cobertura e fundamentação das respostas."""

from __future__ import annotations

from dataclasses import dataclass

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.llm.schemas import DriverInstructions, RouteAnswer


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    """Pontua uma resposta e explica problemas encontrados."""

    score: float
    valid: bool
    issues: tuple[str, ...]


def assess_instructions(
    problem: RoutingProblem,
    chromosome: RouteChromosome,
    response: DriverInstructions,
) -> QualityAssessment:
    """Confere cobertura, veículos e sequência exata das instruções."""
    issues: list[str] = []
    expected = {
        problem.vehicles[index].id: route
        for index, route in enumerate(chromosome.routes)
        if route
    }
    generated = {route.vehicle_id: route for route in response.routes}
    unknown_vehicles = set(generated) - set(expected)
    missing_vehicles = set(expected) - set(generated)
    if unknown_vehicles:
        issues.append(f"Veículos desconhecidos: {sorted(unknown_vehicles)}")
    if missing_vehicles:
        issues.append(f"Veículos ausentes: {sorted(missing_vehicles)}")

    correct_stops = 0
    total_stops = sum(len(route) for route in expected.values())
    for vehicle_id, expected_deliveries in expected.items():
        if vehicle_id not in generated:
            continue
        route = generated[vehicle_id]
        generated_deliveries = tuple(step.delivery_id for step in route.steps)
        generated_stops = tuple(step.stop for step in route.steps)
        expected_stops = tuple(range(1, len(expected_deliveries) + 1))
        if generated_deliveries != expected_deliveries:
            issues.append(f"Sequência divergente no veículo {vehicle_id}.")
        if generated_stops != expected_stops:
            issues.append(f"Numeração divergente no veículo {vehicle_id}.")
        correct_stops += sum(
            expected_item == generated_item
            for expected_item, generated_item in zip(
                expected_deliveries,
                generated_deliveries,
                strict=False,
            )
        )
    coverage = correct_stops / total_stops if total_stops else 1.0
    score = max(0.0, coverage - 0.1 * len(issues))
    return QualityAssessment(score, not issues, tuple(issues))


def assess_answer(problem: RoutingProblem, response: RouteAnswer) -> QualityAssessment:
    """Confere se todas as evidências citadas existem no cenário."""
    delivery_ids = set(problem.delivery_ids)
    vehicle_ids = {vehicle.id for vehicle in problem.vehicles}
    unknown_deliveries = set(response.evidence_delivery_ids) - delivery_ids
    unknown_vehicles = set(response.evidence_vehicle_ids) - vehicle_ids
    issues = []
    if unknown_deliveries:
        issues.append(f"Entregas desconhecidas: {sorted(unknown_deliveries)}")
    if unknown_vehicles:
        issues.append(f"Veículos desconhecidos: {sorted(unknown_vehicles)}")
    score = max(0.0, 1.0 - 0.5 * len(issues))
    return QualityAssessment(score, not issues, tuple(issues))
