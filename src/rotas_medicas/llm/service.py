"""Casos de uso de linguagem natural sobre um plano otimizado."""

from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.llm.prompts import (
    SYSTEM_PROMPT,
    instructions_prompt,
    question_prompt,
    report_prompt,
    route_context,
)
from rotas_medicas.llm.provider import LLMProvider
from rotas_medicas.llm.quality import (
    QualityAssessment,
    assess_answer,
    assess_instructions,
)
from rotas_medicas.llm.schemas import (
    DeliveryStep,
    DriverGuidance,
    DriverInstructions,
    EfficiencyComparison,
    EfficiencyNarrative,
    EfficiencyReport,
    RouteAnswer,
    VehicleInstructions,
)
from rotas_medicas.optimization import (
    FitnessEvaluation,
    compare_with_best_baseline,
)

_GENERAL_GUIDANCE = {
    "conferencia_carga": "Confira a carga e a documentação antes da saída.",
    "comunicacao_central": "Comunique impedimentos à central de operação.",
    "registro_entrega": "Registre a conclusão de cada entrega.",
}
_CRITICAL_INSTRUCTIONS = {
    "integridade_carga": "Priorize a integridade da carga durante o transporte.",
    "confirmacao_recebimento": "Confirme o recebimento da carga prioritária.",
    "prioridade_operacional": "Atenda esta entrega com prioridade operacional.",
}
_STANDARD_INSTRUCTIONS = {
    "confirmacao_destino": "Confirme o destino antes de concluir a entrega.",
    "registro_entrega": "Registre a conclusão da entrega.",
    "integridade_carga": "Preserve a integridade da carga durante o transporte.",
}
_ALERTS = {
    "nao_alterar_sequencia": "Não altere a sequência sem autorização da operação.",
    "comunicar_impedimento": "Comunique qualquer impedimento à central de operação.",
    "conferir_capacidade": "Confira a carga com a capacidade registrada do veículo.",
}


class LLMValidationError(ValueError):
    """Indica que a resposta estruturada contradiz o plano calculado."""


class RouteLanguageService:
    """Gera conteúdo sem delegar decisões de roteamento à LLM."""

    def __init__(
        self,
        problem: RoutingProblem,
        chromosome: RouteChromosome,
        evaluation: FitnessEvaluation,
        provider: LLMProvider,
    ) -> None:
        if not evaluation.feasible:
            raise ValueError("A LLM só pode explicar um plano final viável.")
        self._problem = problem
        self._chromosome = chromosome
        self._evaluation = evaluation
        self._provider = provider
        self._context = route_context(problem, chromosome, evaluation)

    def generate_driver_instructions(
        self,
    ) -> tuple[DriverInstructions, QualityAssessment]:
        """Gera instruções e bloqueia divergências de rota ou sequência."""
        guidance = self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=instructions_prompt(self._context),
            response_model=DriverGuidance,
        )
        deliveries = self._problem.deliveries_by_id
        routes = tuple(
            VehicleInstructions(
                vehicle_id=self._problem.vehicles[index].id,
                summary="Execute as entregas na ordem definida pelo otimizador.",
                steps=tuple(
                    DeliveryStep(
                        stop=stop,
                        delivery_id=delivery_id,
                        destination=deliveries[delivery_id].destination,
                        priority=deliveries[delivery_id].priority.value,
                        instruction=(
                            _CRITICAL_INSTRUCTIONS[guidance.critical_focus]
                            if deliveries[delivery_id].priority.value
                            in {"critica", "alta"}
                            else _STANDARD_INSTRUCTIONS[guidance.standard_focus]
                        ),
                    )
                    for stop, delivery_id in enumerate(route, start=1)
                ),
                alerts=(_ALERTS[guidance.alert_focus],),
            )
            for index, route in enumerate(self._chromosome.routes)
            if route
        )
        response = DriverInstructions(
            title="Instruções operacionais do plano otimizado",
            general_guidance=(_GENERAL_GUIDANCE[guidance.operational_focus],),
            routes=routes,
        )
        quality = assess_instructions(self._problem, self._chromosome, response)
        if not quality.valid:
            raise LLMValidationError("; ".join(quality.issues))
        return response, quality

    def generate_efficiency_report(
        self,
        period: Literal["diario", "semanal"] = "diario",
    ) -> EfficiencyReport:
        """Gera relatório sem aceitar métricas calculadas pelo modelo."""
        narrative = self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=report_prompt(self._context, period),
            response_model=EfficiencyNarrative,
        )
        comparison = compare_with_best_baseline(self._problem, self._evaluation)
        direction = "economia" if comparison.distance_savings_km >= 0 else "aumento"
        return EfficiencyReport(
            period=period,
            title=narrative.title,
            executive_summary=(
                "O plano otimizado utiliza "
                f"{comparison.optimized_vehicles} veículo(s), "
                f"percorre {comparison.optimized_distance_km:.2f} km e tem custo "
                f"operacional estimado de {comparison.optimized_operating_cost:.2f}."
            ),
            highlights=(
                f"Comparação com {comparison.baseline_name}: {direction} de "
                f"{abs(comparison.distance_savings_km):.2f} km "
                f"({abs(comparison.distance_savings_percent):.2f}%).",
                f"Variação favorável de custo: "
                f"{comparison.operating_cost_savings:.2f} "
                f"({comparison.operating_cost_savings_percent:.2f}%).",
                f"Variação favorável de tempo estimado: "
                f"{comparison.time_savings_minutes:.2f} min "
                f"({comparison.time_savings_percent:.2f}%).",
                f"Veículos utilizados: {comparison.optimized_vehicles}; baseline: "
                f"{comparison.baseline_vehicles}.",
            ),
            risks=(
                "O tempo calculado é estimado e não considera trânsito em tempo real.",
                "Os cenários usam dados sintéticos e devem ser recalibrados com dados "
                "operacionais antes do uso real.",
            ),
            suggested_improvements=narrative.suggested_improvements,
            metrics_interpretation=(
                "Valores positivos de economia representam melhora sobre o baseline; "
                "valores negativos representam piora.",
                "O tempo é uma estimativa baseada em velocidade média e tempo de "
                "serviço, sem trânsito em tempo real.",
            ),
            comparison=EfficiencyComparison.model_validate(asdict(comparison)),
        )

    def answer_question(
        self,
        question: str,
    ) -> tuple[RouteAnswer, QualityAssessment]:
        """Responde e rejeita IDs de evidência inexistentes."""
        if not question.strip():
            raise ValueError("A pergunta não pode ser vazia.")
        response = self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=question_prompt(self._context, question),
            response_model=RouteAnswer,
        )
        quality = assess_answer(self._problem, response)
        if not quality.valid:
            raise LLMValidationError("; ".join(quality.issues))
        response = response.model_copy(
            update={
                "evidence_delivery_ids": tuple(
                    dict.fromkeys(
                        response.evidence_delivery_ids
                        + tuple(
                            delivery_id
                            for delivery_id in self._problem.deliveries_by_id
                            if delivery_id in response.answer
                        )
                    )
                ),
                "evidence_vehicle_ids": tuple(
                    dict.fromkeys(
                        response.evidence_vehicle_ids
                        + tuple(
                            vehicle.id
                            for vehicle in self._problem.vehicles
                            if vehicle.id in response.answer
                        )
                    )
                ),
            }
        )
        return response, quality
