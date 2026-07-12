"""Heurísticas determinísticas usadas como referência experimental."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import pairwise

from rotas_medicas.domain import Delivery, RoutingProblem, Vehicle
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization.distance import DistanceMatrix

Baseline = Callable[[RoutingProblem], RouteChromosome]


def _route_distance(
    problem: RoutingProblem,
    distances: DistanceMatrix,
    route: Iterable[str],
) -> float:
    delivery_ids = tuple(route)
    if not delivery_ids:
        return 0.0
    points = (problem.depot.id, *delivery_ids, problem.depot.id)
    return sum(distances.between(first, second) for first, second in pairwise(points))


def _can_append(
    problem: RoutingProblem,
    distances: DistanceMatrix,
    vehicle: Vehicle,
    route: list[str],
    current_load: float,
    delivery: Delivery,
) -> bool:
    candidate_distance = _route_distance(
        problem,
        distances,
        (*route, delivery.id),
    )
    return (
        vehicle.available
        and current_load + delivery.demand <= vehicle.capacity
        and candidate_distance <= vehicle.range_km
    )


def _fallback_vehicle(
    problem: RoutingProblem,
    distances: DistanceMatrix,
    routes: list[list[str]],
    loads: list[float],
    delivery: Delivery,
) -> int:
    """Escolhe a atribuição com menor violação quando não há opção viável."""

    def violation_score(index: int) -> tuple[float, int]:
        vehicle = problem.vehicles[index]
        candidate_distance = _route_distance(
            problem,
            distances,
            (*routes[index], delivery.id),
        )
        capacity_excess = max(0.0, loads[index] + delivery.demand - vehicle.capacity)
        range_excess = max(0.0, candidate_distance - vehicle.range_km)
        unavailable = 1.0 if not vehicle.available else 0.0
        score = unavailable * 100_000 + capacity_excess * 10_000 + range_excess * 10_000
        return score, index

    return min(range(len(problem.vehicles)), key=violation_score)


def _assign_in_order(
    problem: RoutingProblem,
    ordered_deliveries: Iterable[Delivery],
    choose_best_distance: bool,
) -> RouteChromosome:
    distances = DistanceMatrix.from_problem(problem)
    routes: list[list[str]] = [[] for _ in problem.vehicles]
    loads = [0.0 for _ in problem.vehicles]
    for delivery in ordered_deliveries:
        candidates = [
            index
            for index, vehicle in enumerate(problem.vehicles)
            if _can_append(
                problem,
                distances,
                vehicle,
                routes[index],
                loads[index],
                delivery,
            )
        ]
        if not candidates:
            chosen = _fallback_vehicle(problem, distances, routes, loads, delivery)
        elif choose_best_distance:
            chosen = min(
                candidates,
                key=lambda index: (
                    _route_distance(
                        problem,
                        distances,
                        (*routes[index], delivery.id),
                    )
                    - _route_distance(problem, distances, routes[index])
                ),
            )
        else:
            chosen = candidates[0]
        routes[chosen].append(delivery.id)
        loads[chosen] += delivery.demand
    return RouteChromosome(tuple(tuple(route) for route in routes))


def original_order(problem: RoutingProblem) -> RouteChromosome:
    """Aloca a ordem de entrada pelo primeiro veículo que respeita os limites."""
    return _assign_in_order(problem, problem.deliveries, choose_best_distance=False)


def priority_distance(problem: RoutingProblem) -> RouteChromosome:
    """Ordena por criticidade e proximidade e escolhe a inserção mais curta."""
    distances = DistanceMatrix.from_problem(problem)
    ordered = sorted(
        problem.deliveries,
        key=lambda delivery: (
            -problem.priority_weights[delivery.priority],
            distances.between(problem.depot.id, delivery.id),
            delivery.id,
        ),
    )
    return _assign_in_order(problem, ordered, choose_best_distance=True)


def nearest_neighbor(problem: RoutingProblem) -> RouteChromosome:
    """Insere globalmente o vizinho viável mais próximo da ponta de uma rota."""
    distances = DistanceMatrix.from_problem(problem)
    routes: list[list[str]] = [[] for _ in problem.vehicles]
    loads = [0.0 for _ in problem.vehicles]
    remaining = {delivery.id: delivery for delivery in problem.deliveries}

    while remaining:
        candidates: list[tuple[float, int, str]] = []
        for index, vehicle in enumerate(problem.vehicles):
            previous = routes[index][-1] if routes[index] else problem.depot.id
            for delivery in remaining.values():
                if _can_append(
                    problem,
                    distances,
                    vehicle,
                    routes[index],
                    loads[index],
                    delivery,
                ):
                    candidates.append(
                        (
                            distances.between(previous, delivery.id),
                            index,
                            delivery.id,
                        )
                    )

        if candidates:
            _, chosen, delivery_id = min(candidates)
            delivery = remaining[delivery_id]
        else:
            delivery_id = min(remaining)
            delivery = remaining[delivery_id]
            chosen = _fallback_vehicle(problem, distances, routes, loads, delivery)

        routes[chosen].append(delivery_id)
        loads[chosen] += delivery.demand
        del remaining[delivery_id]

    return RouteChromosome(tuple(tuple(route) for route in routes))


BASELINES: dict[str, Baseline] = {
    "ordem_original": original_order,
    "vizinho_mais_proximo": nearest_neighbor,
    "prioridade_distancia": priority_distance,
}
