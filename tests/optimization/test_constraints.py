"""Testes do diagnóstico prévio de inviabilidade."""

from dataclasses import replace
from pathlib import Path

from rotas_medicas.domain import RoutingProblem, load_scenario
from rotas_medicas.optimization import find_feasibility_issues

DATA_PATH = Path(__file__).resolve().parents[2] / "data"


def test_small_scenario_has_no_obvious_feasibility_issue(
    small_problem: RoutingProblem,
) -> None:
    """O cenário positivo deve passar pelas condições necessárias."""
    assert find_feasibility_issues(small_problem) == ()


def test_infeasible_scenario_identifies_oversized_delivery() -> None:
    """A entrega indivisível excessiva deve ser diagnosticada pelo ID."""
    problem = load_scenario(DATA_PATH / "cenario_inviavel.json")
    issues = find_feasibility_issues(problem)

    assert any(
        issue.code == "delivery_exceeds_vehicle_capacity"
        and issue.delivery_id == "ENT-001"
        for issue in issues
    )


def test_no_available_vehicle_is_reported(small_problem: RoutingProblem) -> None:
    """Uma frota totalmente indisponível deve falhar antes da otimização."""
    vehicles = tuple(
        replace(vehicle, available=False) for vehicle in small_problem.vehicles
    )
    problem = replace(small_problem, vehicles=vehicles)

    issues = find_feasibility_issues(problem)

    assert [issue.code for issue in issues] == ["no_available_vehicle"]
