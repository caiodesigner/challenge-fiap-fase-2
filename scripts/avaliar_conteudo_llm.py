"""Registra avaliação humana reproduzível de uma evidência gerada por LLM."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast


def score(value: str) -> int:
    """Valida uma nota inteira na escala definida."""
    parsed = int(value)
    if not 1 <= parsed <= 5:
        raise argparse.ArgumentTypeError("a nota deve estar entre 1 e 5")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--clarity", type=score, required=True)
    parser.add_argument("--usefulness", type=score, required=True)
    parser.add_argument("--safety", type=score, required=True)
    parser.add_argument("--grounding", type=score, required=True)
    parser.add_argument("--decision", choices=["aprovado", "revisar"], required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--reviewer", default="membro-do-grupo")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evidence = cast(
        dict[str, Any],
        json.loads(args.input.read_text(encoding="utf-8")),
    )
    provider = cast(dict[str, Any], evidence.get("provider", {}))
    if provider.get("name") != "ollama":
        raise ValueError("A avaliação final exige uma evidência do provedor Ollama.")

    scores = {
        "clareza": args.clarity,
        "utilidade": args.usefulness,
        "seguranca": args.safety,
        "fundamentacao": args.grounding,
    }
    payload = {
        "evidence_file": str(args.input),
        "scenario_id": evidence.get("scenario_id"),
        "provider": provider,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "reviewer": args.reviewer,
        "scores_1_to_5": scores,
        "average_score": round(sum(scores.values()) / len(scores), 2),
        "decision": args.decision,
        "notes": args.notes,
    }
    destination = args.output or args.input.with_suffix(".avaliacao.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Avaliação registrada: {destination}")


if __name__ == "__main__":
    main()
