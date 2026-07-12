"""Função fitness hospitalar e detalhamento de suas restrições."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields

from rotas_medicas.domain import Delivery, RoutingProblem, Vehicle
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization.distance import DistanceMatrix


@dataclass(frozen=True, slots=True)
class FitnessWeights:
    """Pesos dos objetivos normalizados e das violações duras."""

    distance: float = 1.0
    operating_cost: float = 1.0
    priority_service: float = 2.0
    vehicles_used: float = 0.25
    missing_delivery: float = 100_000.0
    duplicate_delivery: float = 100_000.0
    unknown_delivery: float = 100_000.0
    vehicle_count_mismatch: float = 100_000.0
    unavailable_vehicle: float = 100_000.0
    capacity_excess_unit: float = 10_000.0
    range_excess_km: float = 10_000.0

    def __post_init__(self) -> None:
        if any(getattr(self, field.name) < 0 for field in fields(self)):
            raise ValueError("Pesos da fitness não podem ser negativos.")


@dataclass(frozen=True, slots=True)
class FitnessConfig:
    """Hipóteses operacionais e escalas para normalização."""

    average_speed_kmh: float = 30.0
    service_minutes: float = 10.0
    distance_scale_km: float = 100.0
    operating_cost_scale: float = 1_000.0
    priority_service_scale: float = 1_000.0

    def __post_init__(self) -> None:
        if self.average_speed_kmh <= 0:
            raise ValueError("A velocidade média deve ser positiva.")
        if self.service_minutes < 0:
            raise ValueError("O tempo de serviço não pode ser negativo.")
        if (
            min(
                self.distance_scale_km,
                self.operating_cost_scale,
                self.priority_service_scale,
            )
            <= 0
        ):
            raise ValueError("Escalas de normalização devem ser positivas.")


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    """Violação individual e sua contribuição para a penalidade."""

    code: str
    message: str
    amount: float
    penalty: float
    vehicle_id: str | None = None
    delivery_id: str | None = None


@dataclass(frozen=True, slots=True)
class RouteMetrics:
    """Indicadores calculados para uma rota e seu veículo."""

    vehicle_id: str
    delivery_ids: tuple[str, ...]
    distance_km: float
    load: float
    operating_cost: float
    priority_service_cost: float
    capacity_excess: float
    range_excess_km: float


@dataclass(frozen=True, slots=True)
class FitnessEvaluation:
    """Custo total acompanhado dos componentes que o explicam."""

    total_cost: float
    objective_cost: float
    penalty_cost: float
    feasible: bool
    total_distance_km: float
    total_operating_cost: float
    total_priority_service_cost: float
    vehicles_used: int
    routes: tuple[RouteMetrics, ...]
    violations: tuple[ConstraintViolation, ...]


class RoutingFitness:
    """Avalia cromossomos de rotas como um problema de minimização."""

    def __init__(
        self,
        problem: RoutingProblem,
        weights: FitnessWeights | None = None,
        config: FitnessConfig | None = None,
        distances: DistanceMatrix | None = None,
    ) -> None:
        self._problem = problem
        self._weights = weights or FitnessWeights()
        self._config = config or FitnessConfig()
        self._distances = distances or DistanceMatrix.from_problem(problem)

    def __call__(self, chromosome: RouteChromosome) -> float:
        """Permite injetar a instância diretamente no motor genético."""
        return self.evaluate(chromosome).total_cost

    def evaluate(self, chromosome: RouteChromosome) -> FitnessEvaluation:
        """Calcula objetivos, métricas e penalidades do cromossomo."""
        violations = self._coverage_violations(chromosome)
        route_metrics: list[RouteMetrics] = []
        for route_index, route in enumerate(chromosome.routes):
            if route_index >= len(self._problem.vehicles):
                break
            vehicle = self._problem.vehicles[route_index]
            valid_deliveries = tuple(
                self._problem.deliveries_by_id[delivery_id]
                for delivery_id in route
                if delivery_id in self._problem.deliveries_by_id
            )
            metrics, route_violations = self._evaluate_route(vehicle, valid_deliveries)
            route_metrics.append(metrics)
            violations.extend(route_violations)

        total_distance = sum(route.distance_km for route in route_metrics)
        total_operating = sum(route.operating_cost for route in route_metrics)
        total_priority = sum(route.priority_service_cost for route in route_metrics)
        vehicles_used = sum(bool(route.delivery_ids) for route in route_metrics)
        objective = (
            self._weights.distance * total_distance / self._config.distance_scale_km
            + self._weights.operating_cost
            * total_operating
            / self._config.operating_cost_scale
            + self._weights.priority_service
            * total_priority
            / self._config.priority_service_scale
            + self._weights.vehicles_used * vehicles_used / len(self._problem.vehicles)
        )
        penalty = sum(violation.penalty for violation in violations)
        return FitnessEvaluation(
            total_cost=objective + penalty,
            objective_cost=objective,
            penalty_cost=penalty,
            feasible=not violations,
            total_distance_km=total_distance,
            total_operating_cost=total_operating,
            total_priority_service_cost=total_priority,
            vehicles_used=vehicles_used,
            routes=tuple(route_metrics),
            violations=tuple(violations),
        )

    def _coverage_violations(
        self,
        chromosome: RouteChromosome,
    ) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []
        if chromosome.vehicle_count != len(self._problem.vehicles):
            amount = abs(chromosome.vehicle_count - len(self._problem.vehicles))
            violations.append(
                ConstraintViolation(
                    "vehicle_count_mismatch",
                    "O cromossomo não representa toda a frota do cenário.",
                    float(amount),
                    amount * self._weights.vehicle_count_mismatch,
                )
            )

        expected = set(self._problem.delivery_ids)
        counts = Counter(chromosome.delivery_ids)
        for delivery_id in sorted(expected - set(counts)):
            violations.append(
                ConstraintViolation(
                    "missing_delivery",
                    f"A entrega {delivery_id} não foi incluída no plano.",
                    1.0,
                    self._weights.missing_delivery,
                    delivery_id=delivery_id,
                )
            )
        for delivery_id in sorted(set(counts) - expected):
            violations.append(
                ConstraintViolation(
                    "unknown_delivery",
                    f"A entrega {delivery_id} não pertence ao cenário.",
                    1.0,
                    self._weights.unknown_delivery,
                    delivery_id=delivery_id,
                )
            )
        for delivery_id, count in sorted(counts.items()):
            if count > 1:
                amount = count - 1
                violations.append(
                    ConstraintViolation(
                        "duplicate_delivery",
                        f"A entrega {delivery_id} aparece mais de uma vez.",
                        float(amount),
                        amount * self._weights.duplicate_delivery,
                        delivery_id=delivery_id,
                    )
                )
        return violations

    def _evaluate_route(
        self,
        vehicle: Vehicle,
        deliveries: tuple[Delivery, ...],
    ) -> tuple[RouteMetrics, list[ConstraintViolation]]:
        distance, priority_service = self._route_distance_and_priority(deliveries)
        load = sum(delivery.demand for delivery in deliveries)
        used = bool(deliveries)
        operating_cost = (
            vehicle.fixed_cost + distance * vehicle.cost_per_km if used else 0.0
        )
        capacity_excess = max(0.0, load - vehicle.capacity)
        range_excess = max(0.0, distance - vehicle.range_km)
        violations: list[ConstraintViolation] = []
        if used and not vehicle.available:
            violations.append(
                ConstraintViolation(
                    "unavailable_vehicle",
                    f"O veículo {vehicle.id} não está disponível.",
                    1.0,
                    self._weights.unavailable_vehicle,
                    vehicle_id=vehicle.id,
                )
            )
        if capacity_excess > 0:
            violations.append(
                ConstraintViolation(
                    "capacity_exceeded",
                    f"A rota do veículo {vehicle.id} excede sua capacidade.",
                    capacity_excess,
                    capacity_excess * self._weights.capacity_excess_unit,
                    vehicle_id=vehicle.id,
                )
            )
        if range_excess > 0:
            violations.append(
                ConstraintViolation(
                    "range_exceeded",
                    f"A rota do veículo {vehicle.id} excede sua autonomia.",
                    range_excess,
                    range_excess * self._weights.range_excess_km,
                    vehicle_id=vehicle.id,
                )
            )
        return (
            RouteMetrics(
                vehicle.id,
                tuple(delivery.id for delivery in deliveries),
                distance,
                load,
                operating_cost,
                priority_service,
                capacity_excess,
                range_excess,
            ),
            violations,
        )

    def _route_distance_and_priority(
        self,
        deliveries: tuple[Delivery, ...],
    ) -> tuple[float, float]:
        if not deliveries:
            return 0.0, 0.0

        previous_id = self._problem.depot.id
        distance = 0.0
        elapsed_minutes = 0.0
        priority_service = 0.0
        for delivery in deliveries:
            leg_distance = self._distances.between(previous_id, delivery.id)
            distance += leg_distance
            elapsed_minutes += leg_distance / self._config.average_speed_kmh * 60
            priority_weight = self._problem.priority_weights[delivery.priority]
            lateness = (
                max(0.0, elapsed_minutes - delivery.target_minutes)
                if delivery.target_minutes is not None
                else 0.0
            )
            priority_service += priority_weight * (elapsed_minutes + 2 * lateness)
            elapsed_minutes += self._config.service_minutes
            previous_id = delivery.id

        distance += self._distances.between(previous_id, self._problem.depot.id)
        return distance, priority_service
