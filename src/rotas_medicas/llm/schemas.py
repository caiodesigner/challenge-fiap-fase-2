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


class EfficiencyReport(StrictModel):
    """Relatório gerencial diário ou semanal."""

    period: Literal["diario", "semanal"]
    title: str = Field(min_length=1)
    executive_summary: str = Field(min_length=1)
    highlights: tuple[str, ...]
    risks: tuple[str, ...]
    suggested_improvements: tuple[str, ...]
    metrics_interpretation: tuple[str, ...]


class RouteAnswer(StrictModel):
    """Resposta fundamentada a uma pergunta sobre o plano."""

    answer: str = Field(min_length=1)
    evidence_delivery_ids: tuple[str, ...] = ()
    evidence_vehicle_ids: tuple[str, ...] = ()
    caveat: str | None = None
