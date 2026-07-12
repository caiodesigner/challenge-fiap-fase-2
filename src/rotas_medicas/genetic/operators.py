"""Operadores genéticos especializados em permutações e múltiplas rotas."""

from __future__ import annotations

import random
from collections.abc import Sequence

from rotas_medicas.genetic.chromosome import RouteChromosome


def _validate_compatible_parents(
    first: RouteChromosome,
    second: RouteChromosome,
) -> None:
    if first.vehicle_count != second.vehicle_count:
        raise ValueError("Os pais devem representar a mesma quantidade de veículos.")
    if not first.contains_exactly(second.delivery_ids):
        raise ValueError("Os pais devem conter o mesmo conjunto de entregas.")


def _ordered_child(
    primary: Sequence[str],
    secondary: Sequence[str],
    start: int,
    end: int,
) -> tuple[str, ...]:
    """Constrói um descendente pelo crossover de ordem (OX)."""
    child: list[str | None] = [None] * len(primary)
    child[start:end] = primary[start:end]
    inherited = set(primary[start:end])
    remaining = (item for item in secondary if item not in inherited)
    for index, item in enumerate(child):
        if item is None:
            child[index] = next(remaining)
    return tuple(item for item in child if item is not None)


def order_crossover(
    first: RouteChromosome,
    second: RouteChromosome,
    rng: random.Random,
) -> tuple[RouteChromosome, RouteChromosome]:
    """Cruza a ordem das entregas e herda a divisão de rotas de cada pai."""
    _validate_compatible_parents(first, second)
    first_permutation = first.delivery_ids
    second_permutation = second.delivery_ids
    if len(first_permutation) < 2:
        return first, second

    start, end_inclusive = sorted(rng.sample(range(len(first_permutation)), 2))
    end = end_inclusive + 1
    first_child = _ordered_child(first_permutation, second_permutation, start, end)
    second_child = _ordered_child(second_permutation, first_permutation, start, end)
    return (
        RouteChromosome.from_permutation(first_child, first.route_sizes),
        RouteChromosome.from_permutation(second_child, second.route_sizes),
    )


def swap_mutation(
    chromosome: RouteChromosome,
    rng: random.Random,
) -> RouteChromosome:
    """Troca duas entregas, preservando os tamanhos das rotas."""
    permutation = list(chromosome.delivery_ids)
    if len(permutation) < 2:
        return chromosome
    first, second = rng.sample(range(len(permutation)), 2)
    permutation[first], permutation[second] = permutation[second], permutation[first]
    return RouteChromosome.from_permutation(permutation, chromosome.route_sizes)


def inversion_mutation(
    chromosome: RouteChromosome,
    rng: random.Random,
) -> RouteChromosome:
    """Inverte um trecho da permutação completa."""
    permutation = list(chromosome.delivery_ids)
    if len(permutation) < 2:
        return chromosome
    start, end = sorted(rng.sample(range(len(permutation)), 2))
    permutation[start : end + 1] = reversed(permutation[start : end + 1])
    return RouteChromosome.from_permutation(permutation, chromosome.route_sizes)


def relocation_mutation(
    chromosome: RouteChromosome,
    rng: random.Random,
) -> RouteChromosome:
    """Move uma entrega entre veículos, alterando a divisão das rotas."""
    if chromosome.vehicle_count < 2:
        return inversion_mutation(chromosome, rng)

    routes = [list(route) for route in chromosome.routes]
    source_candidates = [index for index, route in enumerate(routes) if route]
    source = rng.choice(source_candidates)
    destination_candidates = [
        index for index in range(chromosome.vehicle_count) if index != source
    ]
    destination = rng.choice(destination_candidates)
    delivery = routes[source].pop(rng.randrange(len(routes[source])))
    insertion_index = rng.randrange(len(routes[destination]) + 1)
    routes[destination].insert(insertion_index, delivery)
    return RouteChromosome(tuple(tuple(route) for route in routes))


def mutate(
    chromosome: RouteChromosome,
    rng: random.Random,
) -> RouteChromosome:
    """Escolhe uniformemente uma mutação especializada."""
    operator = rng.choice((swap_mutation, inversion_mutation, relocation_mutation))
    return operator(chromosome, rng)
