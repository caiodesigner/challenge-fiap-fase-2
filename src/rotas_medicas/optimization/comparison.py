"""Comparação determinística entre o plano genético e heurísticas de referência."""

from __future__ import annotations

from dataclasses import dataclass

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.optimization.baselines import BASELINES
from rotas_medicas.optimization.fitness import (
    FitnessConfig,
    FitnessEvaluation,
    RoutingFitness,
)


@dataclass(frozen=True, slots=True)
class BaselineComparison:
    """Indicadores de economia calculados contra o melhor baseline viável."""

    baseline_name: str
    optimized_distance_km: float
    baseline_distance_km: float
    distance_savings_km: float
    distance_savings_percent: float
    optimized_operating_cost: float
    baseline_operating_cost: float
    operating_cost_savings: float
    operating_cost_savings_percent: float
    optimized_estimated_minutes: float
    baseline_estimated_minutes: float
    time_savings_minutes: float
    time_savings_percent: float
    optimized_vehicles: int
    baseline_vehicles: int
    vehicles_saved: int


def _percentage(savings: float, reference: float) -> float:
    return savings / reference * 100 if reference else 0.0


def _estimated_minutes(
    problem: RoutingProblem,
    evaluation: FitnessEvaluation,
    config: FitnessConfig,
) -> float:
    travel = evaluation.total_distance_km / config.average_speed_kmh * 60
    service = len(problem.deliveries) * config.service_minutes
    return travel + service


def compare_with_best_baseline(
    problem: RoutingProblem,
    optimized: FitnessEvaluation,
    config: FitnessConfig | None = None,
) -> BaselineComparison:
    """Compara a solução com o baseline viável de menor fitness total."""
    effective_config = config or FitnessConfig()
    fitness = RoutingFitness(problem, config=effective_config)
    candidates = []
    for name, baseline in BASELINES.items():
        evaluation = fitness.evaluate(baseline(problem))
        if evaluation.feasible:
            candidates.append((name, evaluation))
    if not candidates:
        raise ValueError("Nenhum baseline viável está disponível para comparação.")

    baseline_name, reference = min(
        candidates,
        key=lambda item: item[1].total_cost,
    )
    distance_savings = reference.total_distance_km - optimized.total_distance_km
    cost_savings = reference.total_operating_cost - optimized.total_operating_cost
    optimized_minutes = _estimated_minutes(problem, optimized, effective_config)
    baseline_minutes = _estimated_minutes(problem, reference, effective_config)
    time_savings = baseline_minutes - optimized_minutes

    return BaselineComparison(
        baseline_name=baseline_name,
        optimized_distance_km=round(optimized.total_distance_km, 4),
        baseline_distance_km=round(reference.total_distance_km, 4),
        distance_savings_km=round(distance_savings, 4),
        distance_savings_percent=round(
            _percentage(distance_savings, reference.total_distance_km),
            2,
        ),
        optimized_operating_cost=round(optimized.total_operating_cost, 4),
        baseline_operating_cost=round(reference.total_operating_cost, 4),
        operating_cost_savings=round(cost_savings, 4),
        operating_cost_savings_percent=round(
            _percentage(cost_savings, reference.total_operating_cost),
            2,
        ),
        optimized_estimated_minutes=round(optimized_minutes, 2),
        baseline_estimated_minutes=round(baseline_minutes, 2),
        time_savings_minutes=round(time_savings, 2),
        time_savings_percent=round(
            _percentage(time_savings, baseline_minutes),
            2,
        ),
        optimized_vehicles=optimized.vehicles_used,
        baseline_vehicles=reference.vehicles_used,
        vehicles_saved=reference.vehicles_used - optimized.vehicles_used,
    )
