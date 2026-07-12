"""Testes dos operadores genéticos especializados."""

import random

import pytest

from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.genetic.operators import (
    inversion_mutation,
    order_crossover,
    relocation_mutation,
    swap_mutation,
)
from rotas_medicas.genetic.population import create_initial_population

DELIVERIES = tuple(f"E{index}" for index in range(10))


def assert_preserves_deliveries(chromosome: RouteChromosome) -> None:
    """Confirma a invariável estrutural comum a todos os operadores."""
    assert chromosome.contains_exactly(DELIVERIES)
    assert len(chromosome.delivery_ids) == len(DELIVERIES)


def test_initial_population_is_reproducible_and_valid() -> None:
    """A mesma seed deve produzir a mesma população válida."""
    first = create_initial_population(DELIVERIES, 3, 12, random.Random(42))
    second = create_initial_population(DELIVERIES, 3, 12, random.Random(42))

    assert first == second
    assert len(first) == 12
    assert all(chromosome.vehicle_count == 3 for chromosome in first)
    assert all(chromosome.contains_exactly(DELIVERIES) for chromosome in first)


def test_order_crossover_preserves_deliveries_and_route_count() -> None:
    """OX deve gerar duas permutações completas e válidas."""
    first = RouteChromosome.from_permutation(DELIVERIES, (4, 3, 3))
    second = RouteChromosome.from_permutation(tuple(reversed(DELIVERIES)), (2, 5, 3))

    children = order_crossover(first, second, random.Random(7))

    assert children[0].route_sizes == first.route_sizes
    assert children[1].route_sizes == second.route_sizes
    for child in children:
        assert_preserves_deliveries(child)


@pytest.mark.parametrize(
    "operator",
    [swap_mutation, inversion_mutation, relocation_mutation],
)
def test_mutations_preserve_all_deliveries(operator: object) -> None:
    """Nenhuma mutação pode duplicar ou remover uma entrega."""
    chromosome = RouteChromosome.from_permutation(DELIVERIES, (4, 3, 3))
    mutated = operator(chromosome, random.Random(11))  # type: ignore[operator]

    assert_preserves_deliveries(mutated)
    assert mutated.vehicle_count == chromosome.vehicle_count
    assert mutated != chromosome


def test_relocation_changes_vehicle_allocation() -> None:
    """A realocação deve mudar o tamanho de duas rotas."""
    chromosome = RouteChromosome.from_permutation(DELIVERIES, (4, 3, 3))
    mutated = relocation_mutation(chromosome, random.Random(13))

    assert mutated.route_sizes != chromosome.route_sizes


def test_crossover_rejects_incompatible_parents() -> None:
    """Pais de problemas diferentes não podem ser cruzados."""
    first = RouteChromosome((("A", "B"), ("C",)))
    second = RouteChromosome((("A", "B"), ("D",)))

    with pytest.raises(ValueError, match="mesmo conjunto"):
        order_crossover(first, second, random.Random(1))
