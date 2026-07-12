"""Testes da orquestração dos casos de uso."""

from pathlib import Path

import pytest

from rotas_medicas.application import (
    InfeasibleScenarioError,
    RouteApplicationService,
    ScenarioNotFoundError,
    SolutionNotFoundError,
)
from rotas_medicas.genetic import GeneticConfig
from rotas_medicas.llm import RuleBasedProvider

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def service() -> RouteApplicationService:
    """Cria serviço isolado com conteúdo LLM local."""
    return RouteApplicationService(DATA_DIR, RuleBasedProvider())


def test_lists_catalog_with_detected_infeasibility(
    service: RouteApplicationService,
) -> None:
    """Catálogo deve informar dimensões e bloquear o cenário negativo."""
    scenarios = service.list_scenarios()

    assert {scenario.id for scenario in scenarios} == {
        "critico",
        "inviavel",
        "medio",
        "pequeno",
    }
    infeasible = next(item for item in scenarios if item.id == "inviavel")
    assert infeasible.detected_issues
    assert not infeasible.expected_feasible


def test_optimizes_stores_and_explains_solution(
    service: RouteApplicationService,
) -> None:
    """Fluxo de aplicação deve chegar da otimização ao assistente."""
    config = GeneticConfig(
        population_size=30,
        max_generations=40,
        elite_count=2,
        tournament_size=3,
        stagnation_generations=15,
        seed=101,
    )

    record = service.optimize("pequeno", config)
    loaded = service.get_solution(record.id)
    instructions, instruction_quality = service.generate_instructions(record.id)
    report = service.generate_report(record.id, "diario")
    answer, answer_quality = service.answer_question(record.id, "Quais veículos?")

    assert loaded == record
    assert record.evaluation.feasible
    assert instruction_quality.valid
    assert instructions.routes
    assert report.period == "diario"
    assert answer_quality.valid
    assert answer.evidence_vehicle_ids


def test_rejects_unknown_and_infeasible_scenarios(
    service: RouteApplicationService,
) -> None:
    """Erros de catálogo devem ser específicos e rastreáveis."""
    config = GeneticConfig(population_size=10, max_generations=2, elite_count=1)

    with pytest.raises(ScenarioNotFoundError):
        service.optimize("desconhecido", config)
    with pytest.raises(InfeasibleScenarioError) as error:
        service.optimize("inviavel", config)
    assert error.value.issues


def test_rejects_unknown_solution(service: RouteApplicationService) -> None:
    """IDs efêmeros inexistentes devem falhar claramente."""
    with pytest.raises(SolutionNotFoundError):
        service.get_solution("inexistente")
