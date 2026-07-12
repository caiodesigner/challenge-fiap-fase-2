"""Gráficos SVG leves e reproduzíveis para análise da otimização."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from html import escape
from pathlib import Path

CHART_COLORS = (
    "#2563eb",
    "#dc2626",
    "#16a34a",
    "#9333ea",
    "#ea580c",
    "#0891b2",
)


def write_convergence_chart(
    histories: Mapping[str, Sequence[float]],
    path: str | Path,
    title: str = "Convergência do algoritmo genético",
) -> None:
    """Grava as séries de melhor custo por geração em um SVG."""
    if not histories or any(not values for values in histories.values()):
        raise ValueError("É necessário informar históricos não vazios.")
    if any(
        not math.isfinite(value) for values in histories.values() for value in values
    ):
        raise ValueError("Os históricos devem conter apenas valores finitos.")

    width, height = 960, 540
    left, right, top, bottom = 80, 30, 55, 75
    chart_width = width - left - right
    chart_height = height - top - bottom
    maximum_generation = max(len(values) - 1 for values in histories.values())
    all_values = [value for values in histories.values() for value in values]
    minimum_cost, maximum_cost = min(all_values), max(all_values)
    cost_span = maximum_cost - minimum_cost or 1.0

    def x_position(generation: int) -> float:
        return left + chart_width * generation / max(1, maximum_generation)

    def y_position(cost: float) -> float:
        return top + chart_height * (maximum_cost - cost) / cost_span

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        f"<title>{escape(title)}</title>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="30" font-family="system-ui" font-size="20" '
        f'font-weight="700">{escape(title)}</text>',
    ]
    for tick in range(6):
        ratio = tick / 5
        y = top + chart_height * ratio
        cost = maximum_cost - cost_span * ratio
        elements.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
                f'y2="{y:.2f}" stroke="#e2e8f0"/>',
                f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" '
                f'font-family="system-ui" font-size="11">{cost:.3f}</text>',
            ]
        )
    for index, (label, values) in enumerate(sorted(histories.items())):
        color = CHART_COLORS[index % len(CHART_COLORS)]
        points = " ".join(
            f"{x_position(generation):.2f},{y_position(cost):.2f}"
            for generation, cost in enumerate(values)
        )
        elements.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            'stroke-width="2.2" stroke-linejoin="round"/>'
        )
        legend_x = left + (index % 3) * 270
        legend_y = height - 42 + (index // 3) * 18
        elements.extend(
            [
                f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 22}" '
                f'y2="{legend_y}" stroke="{color}" stroke-width="3"/>',
                f'<text x="{legend_x + 28}" y="{legend_y + 4}" '
                f'font-family="system-ui" font-size="11">{escape(label)}</text>',
            ]
        )
    elements.extend(
        [
            f'<line x1="{left}" y1="{top + chart_height}" x2="{width - right}" '
            f'y2="{top + chart_height}" stroke="#334155"/>',
            f'<text x="{left + chart_width / 2}" y="{height - 12}" '
            'text-anchor="middle" font-family="system-ui" font-size="12">'
            "Geração</text>",
            f'<text x="18" y="{top + chart_height / 2}" text-anchor="middle" '
            'transform="rotate(-90 18 260)" font-family="system-ui" '
            'font-size="12">Melhor custo</text>',
            "</svg>",
        ]
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(elements) + "\n", encoding="utf-8")
