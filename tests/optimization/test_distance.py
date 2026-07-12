"""Testes de distância geográfica e matriz do cenário."""

import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.optimization import DistanceMatrix, haversine_km


def test_haversine_returns_known_scale_and_is_symmetric() -> None:
    """Um grau de longitude no equador mede aproximadamente 111,2 km."""
    forward = haversine_km(0, 0, 0, 1)
    backward = haversine_km(0, 1, 0, 0)

    assert forward == pytest.approx(111.195, rel=1e-4)
    assert backward == pytest.approx(forward)


def test_distance_matrix_covers_depot_and_deliveries(
    small_problem: RoutingProblem,
) -> None:
    """A matriz deve ser simétrica e retornar zero no mesmo ponto."""
    matrix = DistanceMatrix.from_problem(small_problem)
    depot_id = small_problem.depot.id
    delivery_id = small_problem.delivery_ids[0]

    assert matrix.between(depot_id, depot_id) == 0
    assert matrix.between(depot_id, delivery_id) == pytest.approx(
        matrix.between(delivery_id, depot_id)
    )
    assert matrix.between(depot_id, delivery_id) > 0


def test_distance_matrix_rejects_unknown_points(
    small_problem: RoutingProblem,
) -> None:
    """IDs não indexados não podem produzir uma distância silenciosa."""
    matrix = DistanceMatrix.from_problem(small_problem)

    with pytest.raises(KeyError, match="não disponível"):
        matrix.between(small_problem.depot.id, "DESCONHECIDO")
