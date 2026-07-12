"""Painel HTML de indicadores operacionais por rota."""

from __future__ import annotations

import html
from pathlib import Path

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.optimization import FitnessEvaluation


def write_metrics_dashboard(
    problem: RoutingProblem,
    evaluation: FitnessEvaluation,
    path: str | Path,
) -> None:
    """Grava KPIs gerais e utilização de cada veículo em uma página HTML."""
    rows = []
    vehicles = {vehicle.id: vehicle for vehicle in problem.vehicles}
    for route in evaluation.routes:
        vehicle = vehicles[route.vehicle_id]
        load_usage = route.load / vehicle.capacity * 100
        range_usage = route.distance_km / vehicle.range_km * 100
        rows.append(
            "<tr>"
            f"<td>{html.escape(vehicle.description)}</td>"
            f"<td>{len(route.delivery_ids)}</td>"
            f"<td>{route.load:.1f} ({load_usage:.1f}%)</td>"
            f"<td>{route.distance_km:.2f} km ({range_usage:.1f}%)</td>"
            f"<td>{route.operating_cost:.2f}</td>"
            "</tr>"
        )
    status_class = "success" if evaluation.feasible else "warning"
    status = "Plano viável" if evaluation.feasible else "Plano com violações"
    title = html.escape(f"Indicadores — {problem.metadata.name}")
    document = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>
body {{ margin: 0; padding: 32px; background: #f8fafc; color: #172033;
  font-family: system-ui, sans-serif; }}
main {{ max-width: 1050px; margin: auto; }}
.cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
.card, table {{ background: white; border-radius: 10px; box-shadow: 0 2px 12px #0001; }}
.card {{ padding: 18px; }} .card span {{ color: #64748b; font-size: 12px; }}
.card strong {{ display: block; margin-top: 4px; font-size: 23px; }}
.success {{ color: #15803d; }} .warning {{ color: #b45309; }}
table {{ width: 100%; margin-top: 24px; border-collapse: collapse; overflow: hidden; }}
th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
th {{ background: #eef2ff; font-size: 12px; text-transform: uppercase; }}
@media(max-width: 760px) {{ .cards {{ grid-template-columns: 1fr 1fr; }} }}
</style></head><body><main><h1>{title}</h1>
<div class="cards">
<div class="card"><span>Situação</span>
<strong class="{status_class}">{status}</strong></div>
<div class="card"><span>Distância total</span>
<strong>{evaluation.total_distance_km:.2f} km</strong></div>
<div class="card"><span>Custo operacional</span>
<strong>{evaluation.total_operating_cost:.2f}</strong></div>
<div class="card"><span>Veículos utilizados</span>
<strong>{evaluation.vehicles_used}</strong></div>
</div><table><thead><tr><th>Veículo</th><th>Entregas</th><th>Carga</th>
<th>Autonomia</th><th>Custo</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
</main></body></html>"""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
