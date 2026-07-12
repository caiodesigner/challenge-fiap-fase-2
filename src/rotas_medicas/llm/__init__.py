"""Integração segura com LLMs para explicar rotas calculadas."""

from rotas_medicas.llm.provider import (
    LLMProvider,
    OpenAIResponsesProvider,
    QueueProvider,
    RuleBasedProvider,
)
from rotas_medicas.llm.quality import QualityAssessment
from rotas_medicas.llm.schemas import (
    DriverInstructions,
    EfficiencyComparison,
    EfficiencyNarrative,
    EfficiencyReport,
    RouteAnswer,
)
from rotas_medicas.llm.service import LLMValidationError, RouteLanguageService

__all__ = [
    "DriverInstructions",
    "EfficiencyComparison",
    "EfficiencyNarrative",
    "EfficiencyReport",
    "LLMProvider",
    "LLMValidationError",
    "OpenAIResponsesProvider",
    "QualityAssessment",
    "QueueProvider",
    "RouteAnswer",
    "RouteLanguageService",
    "RuleBasedProvider",
]
