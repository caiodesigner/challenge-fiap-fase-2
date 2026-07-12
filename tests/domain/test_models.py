"""Testes das invariantes das entidades do domínio."""

from dataclasses import replace

import pytest

from rotas_medicas.domain import (
    Delivery,
    Depot,
    DestinationType,
    Priority,
    RoutingProblem,
    ScenarioMetadata,
    Vehicle,
)


def metadata() -> ScenarioMetadata:
    """Metadados mínimos para construir um problema de teste."""
    return ScenarioMetadata("teste", "Teste", "Cenário", "2026-01-01", 1, True, None)


def depot() -> Depot:
    """Depósito válido para os testes."""
    return Depot("D1", "Depósito", -23.55, -46.63)


def delivery(identifier: str = "E1") -> Delivery:
    """Entrega válida para os testes."""
    return Delivery(
        identifier,
        "Destino",
        DestinationType.HEALTH_UNIT,
        -23.56,
        -46.64,
        5,
        Priority.CRITICAL,
        60,
        "Medicamentos",
    )


def vehicle(identifier: str = "V1") -> Vehicle:
    """Veículo válido para os testes."""
    return Vehicle(identifier, "Veículo", 20, 50, 10, 1, True)


def problem() -> RoutingProblem:
    """Problema válido com todos os pesos de prioridade."""
    return RoutingProblem(
        metadata(),
        depot(),
        (vehicle(),),
        (delivery(),),
        {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.NORMAL: 2,
            Priority.LOW: 1,
        },
    )


@pytest.mark.parametrize(
    ("latitude", "longitude", "message"),
    [(91, 0, "latitude"), (-91, 0, "latitude"), (0, 181, "longitude")],
)
def test_rejects_invalid_coordinates(
    latitude: float,
    longitude: float,
    message: str,
) -> None:
    """Coordenadas fora do globo devem falhar cedo."""
    with pytest.raises(ValueError, match=message):
        Depot("D", "Depósito", latitude, longitude)


def test_rejects_invalid_depot_delivery_and_vehicle_values() -> None:
    """Campos obrigatórios e limites físicos devem ser positivos."""
    with pytest.raises(ValueError, match="identificador"):
        Depot("", "Depósito", 0, 0)
    with pytest.raises(ValueError, match="demanda"):
        replace(delivery(), demand=0)
    with pytest.raises(ValueError, match="prazo"):
        replace(delivery(), target_minutes=0)
    with pytest.raises(ValueError, match="identificação"):
        replace(delivery(), cargo_description="")
    with pytest.raises(ValueError, match="Capacidade"):
        replace(vehicle(), capacity=0)
    with pytest.raises(ValueError, match="Custos"):
        replace(vehicle(), fixed_cost=-1)


def test_rejects_empty_or_duplicate_problem_collections() -> None:
    """Problemas devem ter frota, entregas e identificadores únicos."""
    valid = problem()
    with pytest.raises(ValueError, match="ao menos um veículo"):
        replace(valid, vehicles=())
    with pytest.raises(ValueError, match="ao menos uma entrega"):
        replace(valid, deliveries=())
    with pytest.raises(ValueError, match="veículo devem ser únicos"):
        replace(valid, vehicles=(vehicle(), vehicle()))
    with pytest.raises(ValueError, match="entrega devem ser únicos"):
        replace(valid, deliveries=(delivery(), delivery()))


def test_rejects_incomplete_or_non_positive_priority_weights() -> None:
    """A fitness depende de um peso válido para toda prioridade."""
    valid = problem()
    with pytest.raises(ValueError, match="Todas as prioridades"):
        replace(valid, priority_weights={Priority.CRITICAL: 4})
    weights = dict(valid.priority_weights)
    weights[Priority.LOW] = 0
    with pytest.raises(ValueError, match="devem ser positivos"):
        replace(valid, priority_weights=weights)


def test_problem_exposes_immutable_indexes() -> None:
    """Coleções derivadas devem preservar IDs sem permitir alteração."""
    valid = problem()

    assert valid.delivery_ids == ("E1",)
    assert valid.deliveries_by_id["E1"] == delivery()
    with pytest.raises(TypeError):
        valid.deliveries_by_id["E2"] = delivery("E2")  # type: ignore[index]
