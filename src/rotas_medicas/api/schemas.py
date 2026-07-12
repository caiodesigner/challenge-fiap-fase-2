"""Contratos HTTP da API de otimização."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from rotas_medicas.application import ScenarioSummary, SolutionRecord
from rotas_medicas.llm import (
    DriverInstructions,
    EfficiencyReport,
    QualityAssessment,
    RouteAnswer,
)
from rotas_medicas.visualization import build_route_geojson


class APIModel(BaseModel):
    """Base estrita dos corpos recebidos e devolvidos."""

    model_config = ConfigDict(extra="forbid")


class IssueResponse(APIModel):
    """Inviabilidade detectada antes da otimização."""

    code: str
    message: str
    delivery_id: str | None


class ScenarioResponse(APIModel):
    """Item público do catálogo de cenários."""

    id: str
    name: str
    deliveries: int
    vehicles: int
    expected_feasible: bool
    detected_issues: tuple[IssueResponse, ...]

    @classmethod
    def from_summary(cls, summary: ScenarioSummary) -> ScenarioResponse:
        """Converte o modelo de aplicação para o contrato HTTP."""
        return cls(
            id=summary.id,
            name=summary.name,
            deliveries=summary.deliveries,
            vehicles=summary.vehicles,
            expected_feasible=summary.expected_feasible,
            detected_issues=tuple(
                IssueResponse(
                    code=issue.code,
                    message=issue.message,
                    delivery_id=issue.delivery_id,
                )
                for issue in summary.detected_issues
            ),
        )


class OptimizationRequest(APIModel):
    """Parâmetros seguros expostos pela interface."""

    scenario_id: str = Field(min_length=1, max_length=50)
    population_size: int = Field(default=60, ge=10, le=300)
    max_generations: int = Field(default=120, ge=1, le=1_000)
    crossover_rate: float = Field(default=0.9, ge=0, le=1)
    mutation_rate: float = Field(default=0.25, ge=0, le=1)
    elite_count: int = Field(default=3, ge=1, le=50)
    tournament_size: int = Field(default=4, ge=2, le=50)
    stagnation_generations: int | None = Field(default=40, ge=1, le=1_000)
    seed: int | None = None


class StopResponse(APIModel):
    """Parada na sequência de um veículo."""

    order: int
    delivery_id: str
    destination: str
    priority: str
    demand: float


class RouteResponse(APIModel):
    """Rota e indicadores de utilização do veículo."""

    vehicle_id: str
    vehicle: str
    color_index: int
    stops: tuple[StopResponse, ...]
    load: float
    capacity: float
    load_usage_percent: float
    distance_km: float
    range_km: float
    range_usage_percent: float
    operating_cost: float


class MetricsResponse(APIModel):
    """Indicadores globais da solução."""

    feasible: bool
    total_cost: float
    objective_cost: float
    penalty_cost: float
    distance_km: float
    operating_cost: float
    priority_service_cost: float
    vehicles_used: int
    generations_executed: int
    stop_reason: str


class SolutionResponse(APIModel):
    """Resultado completo necessário para desenhar a interface."""

    solution_id: str
    scenario_id: str
    scenario_name: str
    metrics: MetricsResponse
    routes: tuple[RouteResponse, ...]
    geojson: dict[str, Any]
    best_cost_history: tuple[float, ...]

    @classmethod
    def from_record(cls, record: SolutionRecord) -> SolutionResponse:
        """Converte domínio e métricas sem pedir cálculos ao frontend."""
        deliveries = record.problem.deliveries_by_id
        routes = []
        for index, delivery_ids in enumerate(record.chromosome.routes):
            vehicle = record.problem.vehicles[index]
            metrics = record.evaluation.routes[index]
            routes.append(
                RouteResponse(
                    vehicle_id=vehicle.id,
                    vehicle=vehicle.description,
                    color_index=index,
                    stops=tuple(
                        StopResponse(
                            order=stop,
                            delivery_id=delivery_id,
                            destination=deliveries[delivery_id].destination,
                            priority=deliveries[delivery_id].priority.value,
                            demand=deliveries[delivery_id].demand,
                        )
                        for stop, delivery_id in enumerate(delivery_ids, start=1)
                    ),
                    load=metrics.load,
                    capacity=vehicle.capacity,
                    load_usage_percent=metrics.load / vehicle.capacity * 100,
                    distance_km=metrics.distance_km,
                    range_km=vehicle.range_km,
                    range_usage_percent=metrics.distance_km / vehicle.range_km * 100,
                    operating_cost=metrics.operating_cost,
                )
            )
        result = record.genetic_result
        return cls(
            solution_id=record.id,
            scenario_id=record.problem.metadata.id,
            scenario_name=record.problem.metadata.name,
            metrics=MetricsResponse(
                feasible=record.evaluation.feasible,
                total_cost=record.evaluation.total_cost,
                objective_cost=record.evaluation.objective_cost,
                penalty_cost=record.evaluation.penalty_cost,
                distance_km=record.evaluation.total_distance_km,
                operating_cost=record.evaluation.total_operating_cost,
                priority_service_cost=record.evaluation.total_priority_service_cost,
                vehicles_used=record.evaluation.vehicles_used,
                generations_executed=result.generations_executed,
                stop_reason=result.stop_reason,
            ),
            routes=tuple(routes),
            geojson=build_route_geojson(record.problem, record.chromosome),
            best_cost_history=tuple(item.best_cost for item in result.history),
        )


class ReportRequest(APIModel):
    """Período do relatório solicitado."""

    period: Literal["diario", "semanal"] = "diario"


class QuestionRequest(APIModel):
    """Pergunta do operador sobre a solução."""

    question: str = Field(min_length=1, max_length=1_000)


class QualityResponse(APIModel):
    """Avaliação determinística exibida junto ao conteúdo da LLM."""

    score: float
    valid: bool
    issues: tuple[str, ...]

    @classmethod
    def from_assessment(cls, quality: QualityAssessment) -> QualityResponse:
        """Converte a avaliação interna para JSON."""
        return cls(score=quality.score, valid=quality.valid, issues=quality.issues)


class InstructionsResponse(APIModel):
    """Instruções e avaliação de qualidade."""

    content: DriverInstructions
    quality: QualityResponse


class ReportResponse(APIModel):
    """Relatório estruturado gerado pelo provedor."""

    content: EfficiencyReport


class AnswerResponse(APIModel):
    """Resposta fundamentada e sua avaliação."""

    content: RouteAnswer
    quality: QualityResponse
