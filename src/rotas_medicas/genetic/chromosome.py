"""Representação genética de um plano com múltiplas rotas."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import chain


@dataclass(frozen=True, slots=True)
class RouteChromosome:
    """Associa cada veículo, por posição, a uma sequência de entregas.

    Uma rota vazia representa um veículo não utilizado. O cromossomo não conhece
    capacidade, autonomia ou prioridade; essas regras pertencem à avaliação.
    """

    routes: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        """Impede representações ambíguas ou estruturalmente inválidas."""
        if not self.routes:
            raise ValueError("O cromossomo deve possuir ao menos uma rota.")

        delivery_ids = self.delivery_ids
        if not delivery_ids:
            raise ValueError("O cromossomo deve possuir ao menos uma entrega.")
        if any(not delivery_id for delivery_id in delivery_ids):
            raise ValueError("Identificadores de entrega não podem ser vazios.")
        if len(set(delivery_ids)) != len(delivery_ids):
            raise ValueError("Uma entrega não pode aparecer mais de uma vez.")

    @property
    def delivery_ids(self) -> tuple[str, ...]:
        """Retorna a permutação completa, na ordem das rotas."""
        return tuple(chain.from_iterable(self.routes))

    @property
    def route_sizes(self) -> tuple[int, ...]:
        """Retorna quantas entregas estão associadas a cada veículo."""
        return tuple(len(route) for route in self.routes)

    @property
    def vehicle_count(self) -> int:
        """Retorna a quantidade de posições de veículo representadas."""
        return len(self.routes)

    @classmethod
    def from_permutation(
        cls,
        permutation: Sequence[str],
        route_sizes: Sequence[int],
    ) -> RouteChromosome:
        """Divide uma permutação conforme o tamanho informado para cada rota."""
        if not route_sizes:
            raise ValueError("É necessário informar ao menos uma rota.")
        if any(size < 0 for size in route_sizes):
            raise ValueError("Tamanhos de rota não podem ser negativos.")
        if sum(route_sizes) != len(permutation):
            raise ValueError("A soma das rotas deve cobrir toda a permutação.")

        routes: list[tuple[str, ...]] = []
        start = 0
        for size in route_sizes:
            end = start + size
            routes.append(tuple(permutation[start:end]))
            start = end
        return cls(tuple(routes))

    def contains_exactly(self, delivery_ids: Iterable[str]) -> bool:
        """Indica se o cromossomo contém exatamente as entregas fornecidas."""
        expected = tuple(delivery_ids)
        return len(expected) == len(self.delivery_ids) and set(expected) == set(
            self.delivery_ids
        )
