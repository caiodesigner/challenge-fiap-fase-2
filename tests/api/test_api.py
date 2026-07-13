"""Testes HTTP de ponta a ponta da interface FastAPI."""

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from rotas_medicas.api import create_app
from rotas_medicas.application import RouteApplicationService
from rotas_medicas.llm import RuleBasedProvider

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
pytestmark = pytest.mark.anyio


@pytest.fixture
def app() -> FastAPI:
    """Cria aplicação sem acesso ao Ollama ou a serviços externos."""
    service = RouteApplicationService(DATA_DIR, RuleBasedProvider())
    return create_app(service=service)


def client_for(app: FastAPI) -> AsyncClient:
    """Cria cliente ASGI sem abrir porta ou conexão de rede."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def optimize(client: AsyncClient) -> dict[str, Any]:
    """Executa uma otimização pequena reutilizada pelos endpoints."""
    response = await client.post(
        "/api/optimize",
        json={
            "scenario_id": "pequeno",
            "population_size": 30,
            "max_generations": 40,
            "elite_count": 2,
            "tournament_size": 3,
            "stagnation_generations": 15,
            "seed": 101,
        },
    )
    assert response.status_code == 200
    return response.json()


async def test_serves_ui_health_and_openapi(app: FastAPI) -> None:
    """Aplicação deve expor interface, saúde e documentação automática."""
    async with client_for(app) as client:
        index = await client.get("/")
        health = await client.get("/health")
        openapi = await client.get("/openapi.json")

    assert index.status_code == 200
    assert "Otimização de Rotas Médicas" in index.text
    assert "leaflet@1.9.4" in index.text
    assert 'id="optimizationLoading"' in index.text
    assert "Otimizando as rotas" in index.text
    assert "setOptimizing(true)" in index.text
    assert "Gerando instruções" in index.text
    assert "Gerando relatório" in index.text
    assert "setAssistantLoading(true,path)" in index.text
    assert health.json() == {"status": "ok"}
    assert openapi.json()["info"]["title"] == "Otimização de Rotas Médicas"


async def test_lists_scenarios_and_marks_infeasible(app: FastAPI) -> None:
    """Frontend deve receber catálogo suficiente para preencher a seleção."""
    async with client_for(app) as client:
        response = await client.get("/api/scenarios")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 4
    infeasible = next(item for item in items if item["id"] == "inviavel")
    assert infeasible["detected_issues"]


async def test_returns_solution_with_metrics_routes_and_geojson(
    app: FastAPI,
) -> None:
    """Otimização deve retornar todo o estado necessário ao frontend."""
    async with client_for(app) as client:
        solution = await optimize(client)
        loaded = await client.get(f"/api/solutions/{solution['solution_id']}")

    assert solution["metrics"]["feasible"]
    assert solution["metrics"]["distance_km"] > 0
    assert len(solution["routes"]) == 2
    assert solution["geojson"]["type"] == "FeatureCollection"
    assert solution["best_cost_history"]
    assert loaded.status_code == 200
    assert loaded.json()["solution_id"] == solution["solution_id"]


async def test_exposes_all_llm_actions(app: FastAPI) -> None:
    """Interface deve gerar instruções, relatório e resposta fundamentada."""
    async with client_for(app) as client:
        solution = await optimize(client)
        base = f"/api/solutions/{solution['solution_id']}"
        instructions = await client.post(f"{base}/instructions", json={})
        report = await client.post(f"{base}/report", json={"period": "semanal"})
        answer = await client.post(
            f"{base}/question",
            json={"question": "Quais veículos participam?"},
        )

    assert instructions.status_code == 200
    assert instructions.json()["quality"]["valid"]
    assert report.json()["content"]["period"] == "semanal"
    assert report.json()["content"]["comparison"]["baseline_name"]
    assert answer.json()["quality"]["valid"]


async def test_maps_application_and_validation_errors_to_http(app: FastAPI) -> None:
    """Erros esperados devem usar status e mensagens apropriados."""
    async with client_for(app) as client:
        missing = await client.get("/api/solutions/inexistente")
        unknown = await client.post("/api/optimize", json={"scenario_id": "ausente"})
        infeasible = await client.post(
            "/api/optimize",
            json={"scenario_id": "inviavel"},
        )
        invalid = await client.post(
            "/api/optimize",
            json={"scenario_id": "pequeno", "population_size": 1},
        )

    assert missing.status_code == 404
    assert unknown.status_code == 404
    assert infeasible.status_code == 422
    assert infeasible.json()["detail"]["issues"]
    assert invalid.status_code == 422
