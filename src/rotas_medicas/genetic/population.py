"""Inicialização de populações de cromossomos multirrota."""

from __future__ import annotations

import random
from collections.abc import Sequence

from rotas_medicas.genetic.chromosome import RouteChromosome


def create_random_chromosome(
    delivery_ids: Sequence[str],
    vehicle_count: int,
    rng: random.Random,
) -> RouteChromosome:
    """Embaralha entregas e as distribui entre as rotas disponíveis."""
    if not delivery_ids:
        raise ValueError("É necessário informar ao menos uma entrega.")
    if len(set(delivery_ids)) != len(delivery_ids):
        raise ValueError("Os identificadores de entrega devem ser únicos.")
    if vehicle_count < 1:
        raise ValueError("É necessário informar ao menos um veículo.")

    permutation = list(delivery_ids)
    rng.shuffle(permutation)
    routes: list[list[str]] = [[] for _ in range(vehicle_count)]
    for delivery_id in permutation:
        routes[rng.randrange(vehicle_count)].append(delivery_id)

    return RouteChromosome(tuple(tuple(route) for route in routes))


def create_initial_population(
    delivery_ids: Sequence[str],
    vehicle_count: int,
    population_size: int,
    rng: random.Random,
) -> list[RouteChromosome]:
    """Cria uma população válida com o tamanho solicitado."""
    if population_size < 1:
        raise ValueError("O tamanho da população deve ser positivo.")
    return [
        create_random_chromosome(delivery_ids, vehicle_count, rng)
        for _ in range(population_size)
    ]
