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
    DriverInstructions,
    EfficiencyComparison,
    EfficiencyNarrative,
    EfficiencyReport,
    RouteAnswer,
)
from rotas_medicas.optimization import (
    FitnessEvaluation,
    compare_with_best_baseline,
)


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
        response = self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=instructions_prompt(self._context),
            response_model=DriverInstructions,
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
        return EfficiencyReport(
            **narrative.model_dump(),
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
        return response, quality
