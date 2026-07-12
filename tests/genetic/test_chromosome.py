"""Testes da representação genética multirrota."""

import pytest

from rotas_medicas.genetic import RouteChromosome


def test_builds_routes_from_permutation() -> None:
    """A permutação deve ser dividida sem perder entregas."""
    chromosome = RouteChromosome.from_permutation(
        ("A", "B", "C", "D"),
        (2, 0, 2),
    )

    assert chromosome.routes == (("A", "B"), (), ("C", "D"))
    assert chromosome.delivery_ids == ("A", "B", "C", "D")
    assert chromosome.route_sizes == (2, 0, 2)
    assert chromosome.vehicle_count == 3


@pytest.mark.parametrize(
    ("routes", "message"),
    [
        ((), "ao menos uma rota"),
        (((),), "ao menos uma entrega"),
        ((("A", "A"),), "mais de uma vez"),
        ((("",),), "não podem ser vazios"),
    ],
)
def test_rejects_invalid_chromosomes(
    routes: tuple[tuple[str, ...], ...],
    message: str,
) -> None:
    """Representações ambíguas devem falhar imediatamente."""
    with pytest.raises(ValueError, match=message):
        RouteChromosome(routes)


def test_rejects_incompatible_route_sizes() -> None:
    """Toda a permutação deve estar coberta pelas rotas."""
    with pytest.raises(ValueError, match="cobrir toda"):
        RouteChromosome.from_permutation(("A", "B", "C"), (1, 1))
