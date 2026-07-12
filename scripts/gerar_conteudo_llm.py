"""Gera exemplos de instruções, relatório e perguntas sobre as melhores rotas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from rotas_medicas.domain import load_scenario
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.llm import (
    OpenAIResponsesProvider,
    RouteLanguageService,
    RuleBasedProvider,
)
from rotas_medicas.optimization import RoutingFitness

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "reports" / "experiments" / "resultados-iniciais.json"
OUTPUT_DIR = ROOT / "reports" / "llm"


def parse_args() -> argparse.Namespace:
    """Lê provedor, cenários e pasta de saída."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["local", "openai"], default="local")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=["pequeno", "medio"],
        default=["pequeno", "medio"],
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def load_results() -> list[dict[str, Any]]:
    """Carrega resultados já calculados, sem pedir que a LLM escolha rotas."""
    return cast(
        list[dict[str, Any]],
        json.loads(RESULTS_PATH.read_text(encoding="utf-8")),
    )


def main() -> None:
    """Seleciona a melhor rota e executa os três casos de uso de linguagem."""
    args = parse_args()
    results = load_results()
    provider = (
        OpenAIResponsesProvider() if args.provider == "openai" else RuleBasedProvider()
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for scenario_id in args.scenarios:
        problem = load_scenario(ROOT / "data" / f"cenario_{scenario_id}.json")
        candidates = [
            run
            for run in results
            if run["scenario_id"] == scenario_id
            and run["approach"] == "algoritmo_genetico"
            and run["feasible"]
        ]
        best = min(candidates, key=lambda run: float(run["total_cost"]))
        chromosome = RouteChromosome(tuple(tuple(route) for route in best["routes"]))
        evaluation = RoutingFitness(problem).evaluate(chromosome)
        service = RouteLanguageService(problem, chromosome, evaluation, provider)
        instructions, instructions_quality = service.generate_driver_instructions()
        report = service.generate_efficiency_report("diario")
        answer, answer_quality = service.answer_question(
            "Quais veículos participam do plano de entregas?"
        )
        payload = {
            "scenario_id": scenario_id,
            "provider": args.provider,
            "instructions": instructions.model_dump(mode="json"),
            "instructions_quality": {
                "score": instructions_quality.score,
                "valid": instructions_quality.valid,
                "issues": instructions_quality.issues,
            },
            "report": report.model_dump(mode="json"),
            "question_answer": answer.model_dump(mode="json"),
            "answer_quality": {
                "score": answer_quality.score,
                "valid": answer_quality.valid,
                "issues": answer_quality.issues,
            },
        }
        destination = args.output_dir / f"{scenario_id}.json"
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Conteúdo gerado: {destination}")


if __name__ == "__main__":
    main()
