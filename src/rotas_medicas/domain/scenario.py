"""Carregamento dos cenários JSON para entidades do domínio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from rotas_medicas.domain.models import (
    Delivery,
    Depot,
    DestinationType,
    Priority,
    RoutingProblem,
    ScenarioMetadata,
    Vehicle,
)


def _objects(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], data[key])


def load_scenario(path: str | Path) -> RoutingProblem:
    """Carrega um arquivo já validado pelo contrato JSON do projeto."""
    scenario_path = Path(path)
    raw = cast(
        dict[str, Any],
        json.loads(scenario_path.read_text(encoding="utf-8")),
    )
    metadata_data = cast(dict[str, Any], raw["cenario"])
    depot_data = cast(dict[str, Any], raw["deposito"])
    config_data = cast(dict[str, Any], raw["configuracao"])
    priority_data = cast(dict[str, int], config_data["pesos_prioridade"])

    metadata = ScenarioMetadata(
        id=str(metadata_data["id"]),
        name=str(metadata_data["nome"]),
        description=str(metadata_data["descricao"]),
        planning_date=str(metadata_data["data_planejamento"]),
        seed=int(metadata_data["seed"]),
        expected_feasible=bool(metadata_data["viavel_esperado"]),
        expected_infeasibility_reason=metadata_data["motivo_inviabilidade_esperado"],
    )
    depot = Depot(
        id=str(depot_data["id"]),
        name=str(depot_data["nome"]),
        latitude=float(depot_data["latitude"]),
        longitude=float(depot_data["longitude"]),
    )
    vehicles = tuple(
        Vehicle(
            id=str(item["id"]),
            description=str(item["descricao"]),
            capacity=float(item["capacidade"]),
            range_km=float(item["autonomia_km"]),
            fixed_cost=float(item["custo_fixo"]),
            cost_per_km=float(item["custo_por_km"]),
            available=bool(item["disponivel"]),
        )
        for item in _objects(raw, "veiculos")
    )
    deliveries = tuple(
        Delivery(
            id=str(item["id"]),
            destination=str(item["destino"]),
            destination_type=DestinationType(item["tipo_destino"]),
            latitude=float(item["latitude"]),
            longitude=float(item["longitude"]),
            demand=float(item["demanda"]),
            priority=Priority(item["prioridade"]),
            target_minutes=(
                int(item["prazo_alvo_minutos"])
                if item["prazo_alvo_minutos"] is not None
                else None
            ),
            cargo_description=str(item["descricao_carga"]),
        )
        for item in _objects(raw, "entregas")
    )
    priority_weights = {
        priority: int(priority_data[priority.value]) for priority in Priority
    }
    return RoutingProblem(metadata, depot, vehicles, deliveries, priority_weights)
