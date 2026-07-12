"""GeoJSON e mapa interativo das rotas otimizadas."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.optimization import FitnessEvaluation

ROUTE_COLORS = (
    "#2563eb",
    "#dc2626",
    "#16a34a",
    "#9333ea",
    "#ea580c",
    "#0891b2",
    "#4f46e5",
    "#be123c",
)
PRIORITY_COLORS = {
    "critica": "#b91c1c",
    "alta": "#ea580c",
    "normal": "#2563eb",
    "baixa": "#64748b",
}


def build_route_geojson(
    problem: RoutingProblem,
    chromosome: RouteChromosome,
) -> dict[str, Any]:
    """Converte depósito, paradas e trajetos em uma FeatureCollection."""
    if chromosome.vehicle_count != len(problem.vehicles):
        raise ValueError("O cromossomo deve representar toda a frota do cenário.")
    deliveries = problem.deliveries_by_id
    unknown = set(chromosome.delivery_ids) - set(deliveries)
    if unknown:
        raise ValueError(f"Entregas desconhecidas no cromossomo: {sorted(unknown)}")

    features: list[dict[str, Any]] = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [problem.depot.longitude, problem.depot.latitude],
            },
            "properties": {
                "feature_type": "deposito",
                "id": problem.depot.id,
                "name": problem.depot.name,
                "popup": (
                    f"<strong>{html.escape(problem.depot.name)}</strong><br>Depósito"
                ),
            },
        }
    ]
    for route_index, route in enumerate(chromosome.routes):
        vehicle = problem.vehicles[route_index]
        color = ROUTE_COLORS[route_index % len(ROUTE_COLORS)]
        coordinates = [[problem.depot.longitude, problem.depot.latitude]]
        for stop, delivery_id in enumerate(route, start=1):
            delivery = deliveries[delivery_id]
            coordinates.append([delivery.longitude, delivery.latitude])
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [delivery.longitude, delivery.latitude],
                    },
                    "properties": {
                        "feature_type": "entrega",
                        "id": delivery.id,
                        "name": delivery.destination,
                        "vehicle_id": vehicle.id,
                        "route_index": route_index,
                        "stop": stop,
                        "priority": delivery.priority.value,
                        "demand": delivery.demand,
                        "color": color,
                        "priority_color": PRIORITY_COLORS[delivery.priority.value],
                        "popup": (
                            f"<strong>{html.escape(delivery.destination)}</strong><br>"
                            f"Parada {stop} · {html.escape(vehicle.description)}<br>"
                            f"Prioridade: {delivery.priority.value}<br>"
                            f"Demanda: {delivery.demand:g}"
                        ),
                    },
                }
            )
        if route:
            coordinates.append([problem.depot.longitude, problem.depot.latitude])
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates,
                    },
                    "properties": {
                        "feature_type": "rota",
                        "vehicle_id": vehicle.id,
                        "vehicle_name": vehicle.description,
                        "route_index": route_index,
                        "color": color,
                        "stops": len(route),
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def _safe_json(value: object) -> str:
    """Evita que conteúdo textual encerre a tag script do documento."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def write_route_map(
    problem: RoutingProblem,
    chromosome: RouteChromosome,
    evaluation: FitnessEvaluation,
    path: str | Path,
) -> None:
    """Grava um mapa Leaflet com rotas, prioridades e KPIs."""
    geojson = build_route_geojson(problem, chromosome)
    summary = {
        "distance": f"{evaluation.total_distance_km:.2f} km",
        "cost": f"{evaluation.total_cost:.4f}",
        "vehicles": evaluation.vehicles_used,
        "status": "Viável" if evaluation.feasible else "Com violações",
    }
    title = html.escape(f"Rotas otimizadas — {problem.metadata.name}")
    document = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map {{ height: 100%; margin: 0; font-family: system-ui, sans-serif; }}
    .summary {{ position: absolute; z-index: 1000; top: 16px; right: 16px;
      width: 230px; padding: 14px; border-radius: 10px; background: #fffffff2;
      box-shadow: 0 4px 18px #0003; color: #172033; }}
    .summary h1 {{ margin: 0 0 10px; font-size: 16px; }}
    .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .metric {{ padding: 8px; border-radius: 6px; background: #eef2ff; }}
    .metric span {{ display: block; color: #64748b; font-size: 11px; }}
    .metric strong {{ font-size: 14px; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <aside class="summary">
    <h1>{title}</h1>
    <div class="metrics" id="metrics"></div>
  </aside>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const routes = {_safe_json(geojson)};
    const summary = {_safe_json(summary)};
    const map = L.map('map');
    L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);
    const layer = L.geoJSON(routes, {{
      style: feature => ({{ color: feature.properties.color,
        weight: 4, opacity: 0.8 }}),
      pointToLayer: (feature, latlng) => {{
        if (feature.properties.feature_type === 'deposito') {{
          return L.circleMarker(latlng, {{ radius: 10, color: '#111827',
            fillColor: '#facc15', fillOpacity: 1, weight: 3 }});
        }}
        return L.circleMarker(latlng, {{ radius: 7, color: feature.properties.color,
          fillColor: feature.properties.priority_color,
          fillOpacity: 0.95, weight: 3 }});
      }},
      onEachFeature: (feature, item) => {{
        if (feature.properties.popup) item.bindPopup(feature.properties.popup);
        if (feature.properties.feature_type === 'entrega') {{
          item.bindTooltip(String(feature.properties.stop), {{ permanent: true,
            direction: 'center', className: 'stop-label' }});
        }}
      }}
    }}).addTo(map);
    map.fitBounds(layer.getBounds().pad(0.12));
    const labels = {{ distance: 'Distância', cost: 'Fitness',
      vehicles: 'Veículos', status: 'Situação' }};
    document.getElementById('metrics').innerHTML = Object.entries(summary)
      .map(([key, value]) => `<div class="metric"><span>${{labels[key]}}</span>` +
        `<strong>${{value}}</strong></div>`).join('');
  </script>
</body>
</html>
"""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
