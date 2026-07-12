"""Gera mapas, GeoJSON, indicadores e convergência das melhores execuções."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from rotas_medicas.domain import load_scenario
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization import RoutingFitness
from rotas_medicas.visualization import (
    build_route_geojson,
    write_convergence_chart,
    write_metrics_dashboard,
    write_route_map,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "reports" / "experiments" / "resultados-iniciais.json"
DEFAULT_OUTPUT = ROOT / "reports" / "visualizations"


def parse_args() -> argparse.Namespace:
    """Lê os cenários, resultados experimentais e pasta de saída."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["pequeno", "medio"],
        choices=["pequeno", "medio", "critico"],
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_results(path: Path) -> list[dict[str, Any]]:
    """Carrega a saída JSON do executor de experimentos."""
    return cast(
        list[dict[str, Any]],
        json.loads(path.read_text(encoding="utf-8")),
    )


def main() -> None:
    """Seleciona as melhores soluções e gera os artefatos visuais."""
    args = parse_args()
    results = load_results(args.results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for scenario_id in args.scenarios:
        problem = load_scenario(ROOT / "data" / f"cenario_{scenario_id}.json")
        genetic_runs = [
            run
            for run in results
            if run["scenario_id"] == scenario_id
            and run["approach"] == "algoritmo_genetico"
            and run["feasible"]
        ]
        if not genetic_runs:
            raise ValueError(f"Não há execução genética viável para {scenario_id}.")
        best_run = min(genetic_runs, key=lambda run: float(run["total_cost"]))
        routes = tuple(tuple(route) for route in best_run["routes"])
        chromosome = RouteChromosome(routes)
        evaluation = RoutingFitness(problem).evaluate(chromosome)
        prefix = args.output_dir / scenario_id

        write_route_map(
            problem, chromosome, evaluation, prefix.with_suffix(".mapa.html")
        )
        write_metrics_dashboard(
            problem,
            evaluation,
            prefix.with_suffix(".indicadores.html"),
        )
        prefix.with_suffix(".rotas.geojson").write_text(
            json.dumps(
                build_route_geojson(problem, chromosome),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        best_by_configuration: dict[str, dict[str, Any]] = {}
        for run in genetic_runs:
            configuration = str(run["configuration"])
            current = best_by_configuration.get(configuration)
            if current is None or float(run["total_cost"]) < float(
                current["total_cost"]
            ):
                best_by_configuration[configuration] = run
        histories = {
            f"{configuration} · seed {run['seed']}": tuple(
                float(cost) for cost in run["best_cost_history"]
            )
            for configuration, run in best_by_configuration.items()
        }
        write_convergence_chart(
            histories,
            prefix.with_suffix(".convergencia.svg"),
            f"Convergência — {problem.metadata.name}",
        )
        print(f"Visualizações geradas para: {scenario_id}")


if __name__ == "__main__":
    main()
