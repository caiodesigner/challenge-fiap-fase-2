"""Execução e serialização de comparações experimentais."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import fmean, pstdev
from time import perf_counter

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import GeneticAlgorithm, GeneticConfig, RouteChromosome
from rotas_medicas.optimization.baselines import BASELINES
from rotas_medicas.optimization.fitness import FitnessEvaluation, RoutingFitness


@dataclass(frozen=True, slots=True)
class ExperimentRun:
    """Métricas comparáveis de uma execução de algoritmo."""

    scenario_id: str
    approach: str
    configuration: str
    seed: int | None
    elapsed_seconds: float
    total_cost: float
    objective_cost: float
    penalty_cost: float
    feasible: bool
    distance_km: float
    operating_cost: float
    priority_service_cost: float
    vehicles_used: int
    generations_executed: int | None
    stop_reason: str | None
    routes: tuple[tuple[str, ...], ...]
    best_cost_history: tuple[float, ...]


def _record(
    problem: RoutingProblem,
    approach: str,
    configuration: str,
    seed: int | None,
    elapsed_seconds: float,
    chromosome: RouteChromosome,
    evaluation: FitnessEvaluation,
    generations_executed: int | None = None,
    stop_reason: str | None = None,
    best_cost_history: tuple[float, ...] = (),
) -> ExperimentRun:
    return ExperimentRun(
        scenario_id=problem.metadata.id,
        approach=approach,
        configuration=configuration,
        seed=seed,
        elapsed_seconds=elapsed_seconds,
        total_cost=evaluation.total_cost,
        objective_cost=evaluation.objective_cost,
        penalty_cost=evaluation.penalty_cost,
        feasible=evaluation.feasible,
        distance_km=evaluation.total_distance_km,
        operating_cost=evaluation.total_operating_cost,
        priority_service_cost=evaluation.total_priority_service_cost,
        vehicles_used=evaluation.vehicles_used,
        generations_executed=generations_executed,
        stop_reason=stop_reason,
        routes=chromosome.routes,
        best_cost_history=best_cost_history,
    )


def run_experiments(
    problems: Sequence[RoutingProblem],
    genetic_configurations: Mapping[str, GeneticConfig],
    seeds: Sequence[int],
) -> tuple[ExperimentRun, ...]:
    """Executa baselines uma vez e cada configuração genética para cada seed."""
    if not problems:
        raise ValueError("É necessário informar ao menos um cenário.")
    if not genetic_configurations:
        raise ValueError("É necessário informar uma configuração genética.")
    if not seeds:
        raise ValueError("É necessário informar ao menos uma seed.")

    runs: list[ExperimentRun] = []
    for problem in problems:
        fitness = RoutingFitness(problem)
        for name, baseline in BASELINES.items():
            started = perf_counter()
            chromosome = baseline(problem)
            evaluation = fitness.evaluate(chromosome)
            elapsed = perf_counter() - started
            runs.append(
                _record(
                    problem,
                    "baseline",
                    name,
                    None,
                    elapsed,
                    chromosome,
                    evaluation,
                )
            )

        for configuration_name, base_config in genetic_configurations.items():
            for seed in seeds:
                config = replace(base_config, seed=seed)
                algorithm = GeneticAlgorithm(config)
                started = perf_counter()
                result = algorithm.run(
                    problem.delivery_ids,
                    len(problem.vehicles),
                    fitness,
                )
                elapsed = perf_counter() - started
                evaluation = fitness.evaluate(result.best_chromosome)
                runs.append(
                    _record(
                        problem,
                        "algoritmo_genetico",
                        configuration_name,
                        seed,
                        elapsed,
                        result.best_chromosome,
                        evaluation,
                        result.generations_executed,
                        result.stop_reason,
                        tuple(stats.best_cost for stats in result.history),
                    )
                )
    return tuple(runs)


def write_json_report(runs: Sequence[ExperimentRun], path: str | Path) -> None:
    """Grava resultados completos em JSON estável e legível."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps([asdict(run) for run in runs], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_markdown_summary(runs: Sequence[ExperimentRun], path: str | Path) -> None:
    """Resume médias e dispersões por cenário, abordagem e configuração."""
    groups: dict[tuple[str, str, str], list[ExperimentRun]] = defaultdict(list)
    for run in runs:
        groups[(run.scenario_id, run.approach, run.configuration)].append(run)

    lines = [
        "# Resultados iniciais dos experimentos",
        "",
        "| Cenário | Abordagem | Configuração | Execuções | Viáveis | "
        "Custo médio | Desvio | Distância média (km) | Tempo médio (s) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key in sorted(groups):
        scenario, approach, configuration = key
        group = groups[key]
        costs = [run.total_cost for run in group]
        distances = [run.distance_km for run in group]
        elapsed = [run.elapsed_seconds for run in group]
        feasible_count = sum(run.feasible for run in group)
        lines.append(
            f"| {scenario} | {approach} | {configuration} | {len(group)} | "
            f"{feasible_count} | {fmean(costs):.6f} | {pstdev(costs):.6f} | "
            f"{fmean(distances):.3f} | {fmean(elapsed):.4f} |"
        )

    scenarios = sorted({run.scenario_id for run in runs})
    lines.extend(
        [
            "",
            "## Leitura comparativa",
            "",
        ]
    )
    for scenario in scenarios:
        scenario_runs = [run for run in runs if run.scenario_id == scenario]
        baseline_runs = [
            run for run in scenario_runs if run.approach == "baseline" and run.feasible
        ]
        genetic_groups = {
            configuration: [
                run
                for run in scenario_runs
                if run.approach == "algoritmo_genetico"
                and run.configuration == configuration
                and run.feasible
            ]
            for configuration in sorted(
                {
                    run.configuration
                    for run in scenario_runs
                    if run.approach == "algoritmo_genetico"
                }
            )
        }
        genetic_groups = {
            name: group for name, group in genetic_groups.items() if group
        }
        if not baseline_runs or not genetic_groups:
            continue
        best_baseline = min(baseline_runs, key=lambda run: run.total_cost)
        best_genetic_name, best_genetic_runs = min(
            genetic_groups.items(),
            key=lambda item: fmean(run.total_cost for run in item[1]),
        )
        genetic_mean = fmean(run.total_cost for run in best_genetic_runs)
        improvement = (
            best_baseline.total_cost - genetic_mean
        ) / best_baseline.total_cost
        lines.append(
            f"- **{scenario}:** `{best_genetic_name}` obteve custo médio "
            f"{genetic_mean:.6f}, uma redução de {improvement:.2%} sobre o melhor "
            f"baseline (`{best_baseline.configuration}`, "
            f"{best_baseline.total_cost:.6f})."
        )

    lines.extend(
        [
            "",
            "Custos incluem penalidades de restrições. Por isso, resultados "
            "inviáveis não devem ser comparados apenas pela distância.",
        ]
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
