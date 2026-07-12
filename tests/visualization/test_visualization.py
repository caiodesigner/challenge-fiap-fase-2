"""Testes dos artefatos de visualização."""

import json
from pathlib import Path

import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization import RoutingFitness
from rotas_medicas.visualization import (
    build_route_geojson,
    write_convergence_chart,
    write_metrics_dashboard,
    write_route_map,
)


def solution(problem: RoutingProblem) -> tuple[RouteChromosome, RoutingFitness]:
    """Retorna uma solução viável simples para os testes visuais."""
    chromosome = RouteChromosome.from_permutation(problem.delivery_ids, (4, 4))
    return chromosome, RoutingFitness(problem)


def test_geojson_contains_depot_deliveries_and_routes(
    small_problem: RoutingProblem,
) -> None:
    """A coleção deve representar todos os elementos relevantes do mapa."""
    chromosome, _ = solution(small_problem)
    geojson = build_route_geojson(small_problem, chromosome)
    features = geojson["features"]
    feature_types = [feature["properties"]["feature_type"] for feature in features]

    assert geojson["type"] == "FeatureCollection"
    assert feature_types.count("deposito") == 1
    assert feature_types.count("entrega") == 8
    assert feature_types.count("rota") == 2
    assert json.dumps(geojson, ensure_ascii=False)


def test_writes_interactive_map_and_dashboard(
    small_problem: RoutingProblem,
    tmp_path: Path,
) -> None:
    """HTMLs devem incluir mapa, indicadores e informações do cenário."""
    chromosome, fitness = solution(small_problem)
    evaluation = fitness.evaluate(chromosome)
    map_path = tmp_path / "map.html"
    dashboard_path = tmp_path / "dashboard.html"

    write_route_map(small_problem, chromosome, evaluation, map_path)
    write_metrics_dashboard(small_problem, evaluation, dashboard_path)

    map_html = map_path.read_text(encoding="utf-8")
    dashboard_html = dashboard_path.read_text(encoding="utf-8")
    assert "leaflet@1.9.4" in map_html
    assert "ENT-001" in map_html
    assert "Rotas otimizadas" in map_html
    assert "Plano viável" in dashboard_html
    assert "Veículo de distribuição 01" in dashboard_html


def test_writes_convergence_svg(tmp_path: Path) -> None:
    """O gráfico deve conter todas as séries e um documento SVG válido."""
    path = tmp_path / "convergence.svg"

    write_convergence_chart(
        {"balanceada": [10, 8, 7], "exploração": [11, 9, 7.5]},
        path,
    )

    content = path.read_text(encoding="utf-8")
    assert content.startswith("<svg")
    assert "balanceada" in content
    assert "exploração" in content
    assert content.count("<polyline") == 2


@pytest.mark.parametrize(
    "histories",
    [{}, {"vazia": []}, {"inválida": [1, float("inf")]}],
)
def test_rejects_invalid_convergence_histories(
    histories: dict[str, list[float]],
    tmp_path: Path,
) -> None:
    """Séries ausentes ou não finitas devem falhar claramente."""
    with pytest.raises(ValueError, match="histórico"):
        write_convergence_chart(histories, tmp_path / "invalid.svg")


def test_geojson_rejects_incompatible_chromosome(
    small_problem: RoutingProblem,
) -> None:
    """O mapa não deve ocultar incompatibilidade entre solução e cenário."""
    chromosome = RouteChromosome((small_problem.delivery_ids,))

    with pytest.raises(ValueError, match="toda a frota"):
        build_route_geojson(small_problem, chromosome)
