"""Abstrações de provedor e integração com a Responses API da OpenAI."""

from __future__ import annotations

import json
import os
from collections import deque
from collections.abc import Iterable
from typing import Protocol, TypeVar, cast

from openai import OpenAI
from pydantic import BaseModel

from rotas_medicas.llm.schemas import (
    DeliveryStep,
    DriverInstructions,
    EfficiencyReport,
    RouteAnswer,
    VehicleInstructions,
)

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class LLMProvider(Protocol):
    """Contrato mínimo para provedores com saída estruturada."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Gera e valida uma resposta no modelo solicitado."""
        ...


class OpenAIResponsesProvider:
    """Provedor oficial baseado na Responses API e Structured Outputs."""

    def __init__(
        self,
        model: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._model: str = (
            model if model is not None else os.environ.get("OPENAI_MODEL", "gpt-5.6")
        )
        self._client = client or OpenAI()

    @property
    def model(self) -> str:
        """Expõe o modelo efetivamente configurado."""
        return self._model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Solicita saída tipada e rejeita resposta vazia ou recusada."""
        response = self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=response_model,
        )
        if response.output_parsed is None:
            raise RuntimeError("A OpenAI não retornou uma resposta estruturada.")
        return response.output_parsed


class QueueProvider:
    """Provedor determinístico para testes, avaliações e demonstrações locais."""

    def __init__(self, responses: Iterable[BaseModel]) -> None:
        self._responses = deque(responses)
        self.requests: list[tuple[str, str, type[BaseModel]]] = []

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Retorna a próxima resposta somente se ela cumprir o contrato."""
        self.requests.append((system_prompt, user_prompt, response_model))
        if not self._responses:
            raise RuntimeError("Não há resposta determinística disponível.")
        response = self._responses.popleft()
        if not isinstance(response, response_model):
            raise TypeError("A resposta não corresponde ao modelo solicitado.")
        return response


class RuleBasedProvider:
    """Fallback local explícito; não representa uma chamada a uma LLM real."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        """Monta conteúdo previsível a partir do contexto JSON do prompt."""
        del system_prompt
        context = _extract_context(user_prompt)
        if response_model is DriverInstructions:
            response: BaseModel = _rule_based_instructions(context)
        elif response_model is EfficiencyReport:
            response = _rule_based_report(context)
        elif response_model is RouteAnswer:
            response = _rule_based_answer(context)
        else:
            raise TypeError(f"Modelo local não suportado: {response_model.__name__}")
        return cast(ResponseT, response)


def _extract_context(prompt: str) -> dict[str, object]:
    marker = "<dados_json>"
    end_marker = "</dados_json>"
    try:
        content = prompt.split(marker, 1)[1].split(end_marker, 1)[0]
    except IndexError as error:
        raise ValueError("Prompt sem contexto JSON delimitado.") from error
    return cast(dict[str, object], json.loads(content))


def _rule_based_instructions(context: dict[str, object]) -> DriverInstructions:
    routes = cast(list[dict[str, object]], context["rotas"])
    vehicle_routes = []
    for route in routes:
        steps_data = cast(list[dict[str, object]], route["paradas"])
        steps = tuple(
            DeliveryStep.model_validate(
                {
                    "stop": item["ordem"],
                    "delivery_id": item["entrega_id"],
                    "destination": item["destino"],
                    "priority": item["prioridade"],
                    "instruction": (
                        "Confirme o identificador da entrega e registre a conclusão "
                        "antes de seguir para a próxima parada."
                    ),
                }
            )
            for item in steps_data
        )
        vehicle_routes.append(
            VehicleInstructions(
                vehicle_id=str(route["veiculo_id"]),
                summary=f"Realizar {len(steps)} entregas na ordem planejada.",
                steps=steps,
                alerts=("Não alterar a sequência sem autorização da operação.",),
            )
        )
    return DriverInstructions(
        title="Instruções operacionais de entrega",
        general_guidance=(
            "Confira carga e documentação antes da saída.",
            "Comunique imediatamente qualquer impedimento à central.",
        ),
        routes=tuple(vehicle_routes),
    )


def _rule_based_report(context: dict[str, object]) -> EfficiencyReport:
    metrics = cast(dict[str, object], context["metricas"])
    distance = _as_float(metrics["distancia_total_km"])
    operating_cost = _as_float(metrics["custo_operacional"])
    return EfficiencyReport.model_validate(
        {
            "period": context.get("periodo", "diario"),
            "title": "Relatório de eficiência das rotas",
            "executive_summary": (
                f"O plano utiliza {metrics['veiculos_utilizados']} veículos e "
                f"percorre {distance:.2f} km."
            ),
            "highlights": ("Todas as métricas foram calculadas pelo otimizador.",),
            "risks": ("Estimativas não consideram trânsito em tempo real.",),
            "suggested_improvements": (
                "Comparar o planejado com os tempos reais após as entregas.",
            ),
            "metrics_interpretation": (
                f"Custo operacional estimado: {operating_cost:.2f}.",
            ),
        }
    )


def _rule_based_answer(context: dict[str, object]) -> RouteAnswer:
    question = str(context.get("pergunta", ""))
    routes = cast(list[dict[str, object]], context["rotas"])
    vehicle_ids = tuple(str(route["veiculo_id"]) for route in routes)
    return RouteAnswer(
        answer=(
            "Modo local de demonstração: consulte as rotas e métricas estruturadas "
            f"para responder à pergunta: {question}"
        ),
        evidence_vehicle_ids=vehicle_ids,
        caveat="Resposta gerada sem uma LLM externa.",
    )


def _as_float(value: object) -> float:
    if isinstance(value, (int, float, str)):
        return float(value)
    raise TypeError("A métrica deve ser numérica.")
