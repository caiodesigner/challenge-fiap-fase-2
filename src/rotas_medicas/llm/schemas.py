"""Contratos estruturados das respostas produzidas pela LLM."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Modelo que rejeita campos inesperados e mutações posteriores."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class DeliveryStep(StrictModel):
    """Instrução operacional de uma parada da rota."""

    stop: int = Field(ge=1)
    delivery_id: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    priority: Literal["critica", "alta", "normal", "baixa"]
    instruction: str = Field(min_length=1)


class VehicleInstructions(StrictModel):
    """Instruções de uma rota associada a um veículo."""

    vehicle_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    steps: tuple[DeliveryStep, ...]
    alerts: tuple[str, ...] = ()


class DriverInstructions(StrictModel):
    """Conjunto de instruções para toda a equipe de entrega."""

    title: str = Field(min_length=1)
    general_guidance: tuple[str, ...]
    routes: tuple[VehicleInstructions, ...]


class DriverGuidance(StrictModel):
    """Seleções da LLM dentro de orientações previamente fundamentadas."""

    operational_focus: Literal[
        "conferencia_carga", "comunicacao_central", "registro_entrega"
    ]
    critical_focus: Literal[
        "integridade_carga", "confirmacao_recebimento", "prioridade_operacional"
    ]
    standard_focus: Literal[
        "confirmacao_destino", "registro_entrega", "integridade_carga"
    ]
    alert_focus: Literal[
        "nao_alterar_sequencia", "comunicar_impedimento", "conferir_capacidade"
    ]


class EfficiencyNarrative(StrictModel):
    """Interpretação gerencial produzida pelo provedor de linguagem."""

    period: Literal["diario", "semanal"]
    title: str = Field(min_length=1)
    executive_summary: str = Field(min_length=1)
    highlights: tuple[str, ...]
    risks: tuple[str, ...]
    suggested_improvements: tuple[str, ...]
    metrics_interpretation: tuple[str, ...]


class EfficiencyComparison(StrictModel):
    """Economias calculadas pelo sistema, nunca pela LLM."""

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


class EfficiencyReport(EfficiencyNarrative):
    """Relatório final com narrativa e comparação determinística."""

    comparison: EfficiencyComparison


class RouteAnswer(StrictModel):
    """Resposta fundamentada a uma pergunta sobre o plano."""

    answer: str = Field(min_length=1)
    evidence_delivery_ids: tuple[str, ...] = ()
    evidence_vehicle_ids: tuple[str, ...] = ()
    caveat: str | None = None
