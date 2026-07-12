"""Executa baselines e configurações genéticas nos cenários de demonstração."""

from __future__ import annotations

import argparse
from pathlib import Path

from rotas_medicas.domain import load_scenario
from rotas_medicas.genetic import GeneticConfig
from rotas_medicas.optimization.experiments import (
    run_experiments,
    write_json_report,
    write_markdown_summary,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_JSON = ROOT / "reports" / "experiments" / "resultados-iniciais.json"
DEFAULT_MARKDOWN = ROOT / "reports" / "experiments" / "resultados-iniciais.md"


def configurations(profile: str) -> dict[str, GeneticConfig]:
    """Retorna três estratégias com o mesmo orçamento de gerações."""
    population = 40 if profile == "quick" else 80
    generations = 60 if profile == "quick" else 160
    stagnation = 20 if profile == "quick" else 50
    return {
        "exploracao": GeneticConfig(
            population_size=population,
            max_generations=generations,
            crossover_rate=0.95,
            mutation_rate=0.40,
            elite_count=2,
            tournament_size=3,
            stagnation_generations=stagnation,
        ),
        "balanceada": GeneticConfig(
            population_size=population,
            max_generations=generations,
            crossover_rate=0.90,
            mutation_rate=0.25,
            elite_count=3,
            tournament_size=4,
            stagnation_generations=stagnation,
        ),
        "explotacao": GeneticConfig(
            population_size=population,
            max_generations=generations,
            crossover_rate=0.80,
            mutation_rate=0.10,
            elite_count=4,
            tournament_size=6,
            stagnation_generations=stagnation,
        ),
    }


def parse_args() -> argparse.Namespace:
    """Lê opções de cenários, perfil e arquivos de saída."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["pequeno", "medio"],
        choices=["pequeno", "medio", "critico"],
    )
    parser.add_argument("--profile", choices=["quick", "full"], default="full")
    parser.add_argument("--seeds", nargs="+", type=int, default=[11, 22, 33])
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args()


def main() -> None:
    """Executa a matriz experimental solicitada e grava os relatórios."""
    args = parse_args()
    problems = [
        load_scenario(DATA_DIR / f"cenario_{scenario}.json")
        for scenario in args.scenarios
    ]
    runs = run_experiments(problems, configurations(args.profile), args.seeds)
    write_json_report(runs, args.json_output)
    write_markdown_summary(runs, args.markdown_output)
    print(f"Execuções concluídas: {len(runs)}")
    print(f"Resultados completos: {args.json_output}")
    print(f"Resumo: {args.markdown_output}")


if __name__ == "__main__":
    main()
