"""Testes do executor e dos relatórios experimentais."""

import json
from pathlib import Path

import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import GeneticConfig
from rotas_medicas.optimization.experiments import (
    run_experiments,
    write_json_report,
    write_markdown_summary,
)


def test_runs_complete_experiment_matrix(small_problem: RoutingProblem) -> None:
    """Baselines e combinações de configuração e seed devem ser executadas."""
    configurations = {
        "teste_a": GeneticConfig(
            population_size=12,
            max_generations=4,
            elite_count=2,
            tournament_size=3,
            stagnation_generations=None,
        ),
        "teste_b": GeneticConfig(
            population_size=12,
            max_generations=4,
            elite_count=2,
            tournament_size=3,
            stagnation_generations=None,
        ),
    }

    runs = run_experiments([small_problem], configurations, [10, 20])

    assert len(runs) == 7
    assert sum(run.approach == "baseline" for run in runs) == 3
    assert sum(run.approach == "algoritmo_genetico" for run in runs) == 4
    assert all(run.scenario_id == "pequeno" for run in runs)
    assert all(run.elapsed_seconds >= 0 for run in runs)
    genetic_runs = [run for run in runs if run.approach == "algoritmo_genetico"]
    assert all(len(run.best_cost_history) == 5 for run in genetic_runs)


def test_writes_machine_and_human_readable_reports(
    small_problem: RoutingProblem,
    tmp_path: Path,
) -> None:
    """Os dois formatos devem registrar a mesma execução."""
    configuration = GeneticConfig(
        population_size=8,
        max_generations=2,
        elite_count=1,
        tournament_size=2,
        stagnation_generations=None,
    )
    runs = run_experiments([small_problem], {"teste": configuration}, [7])
    json_path = tmp_path / "runs.json"
    markdown_path = tmp_path / "summary.md"

    write_json_report(runs, json_path)
    write_markdown_summary(runs, markdown_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    summary = markdown_path.read_text(encoding="utf-8")
    assert len(payload) == 4
    assert "Resultados iniciais dos experimentos" in summary
    assert "Leitura comparativa" in summary
    assert "redução de" in summary
    assert "algoritmo_genetico" in summary
    assert "pequeno" in summary


@pytest.mark.parametrize(
    ("problems", "configurations", "seeds", "message"),
    [
        ([], {"x": GeneticConfig()}, [1], "cenário"),
        (["problem"], {}, [1], "configuração"),
        (["problem"], {"x": GeneticConfig()}, [], "seed"),
    ],
)
def test_rejects_empty_experiment_dimensions(
    problems: list[object],
    configurations: dict[str, GeneticConfig],
    seeds: list[int],
    message: str,
) -> None:
    """Uma matriz experimental vazia deve falhar com mensagem clara."""
    with pytest.raises(ValueError, match=message):
        run_experiments(  # type: ignore[arg-type]
            problems,
            configurations,
            seeds,
        )
