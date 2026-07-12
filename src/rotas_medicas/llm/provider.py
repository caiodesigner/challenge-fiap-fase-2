"""Abstrações de provedor e integração local com o Ollama."""

from __future__ import annotations

import json
import os
from collections import deque
from collections.abc import Iterable
from typing import Protocol, TypeVar, cast

import httpx
from pydantic import BaseModel

from rotas_medicas.llm.schemas import (
    DriverGuidance,
    EfficiencyNarrative,
    RouteAnswer,
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


class OllamaProvider:
    """Provedor local baseado na API de chat e JSON Schema do Ollama."""

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._model: str = (
            model
            if model is not None
            else os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
        )
        self._host = (
            host
            if host is not None
            else os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        )
        self._client = client or httpx.Client(base_url=self._host, timeout=180.0)

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
        """Solicita saída tipada e valida o JSON devolvido pelo modelo local."""
        try:
            response = self._client.post(
                "/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "format": response_model.model_json_schema(),
                    "options": {"temperature": 0},
                },
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("O Ollama retornou conteúdo vazio.")
            return response_model.model_validate_json(content)
        except httpx.ConnectError as error:
            raise RuntimeError(
                "O Ollama não está acessível. Inicie o serviço e baixe o modelo."
            ) from error
        except httpx.HTTPStatusError as error:
            detail = error.response.text
            raise RuntimeError(
                f"O Ollama recusou a geração ({error.response.status_code}): "
                f"{detail}. Confirme o modelo com `ollama pull {self._model}`."
            ) from error
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Resposta inválida recebida do Ollama.") from error


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
        if response_model is DriverGuidance:
            response: BaseModel = _rule_based_instructions(context)
        elif response_model is EfficiencyNarrative:
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


def _rule_based_instructions(context: dict[str, object]) -> DriverGuidance:
    del context
    return DriverGuidance(
        operational_focus="conferencia_carga",
        critical_focus="integridade_carga",
        standard_focus="registro_entrega",
        alert_focus="nao_alterar_sequencia",
    )


def _rule_based_report(context: dict[str, object]) -> EfficiencyNarrative:
    metrics = cast(dict[str, object], context["metricas"])
    comparison = cast(dict[str, object], context["comparacao_baseline"])
    distance = _as_float(metrics["distancia_total_km"])
    operating_cost = _as_float(metrics["custo_operacional"])
    distance_savings = _as_float(comparison["economia_distancia_km"])
    cost_savings = _as_float(comparison["economia_custo"])
    time_savings = _as_float(comparison["economia_tempo_min"])
    distance_pattern = (
        "Preservar a distribuição atual e acompanhar a distância realizada."
        if distance_savings >= 0
        else "Revisar a sequência para recuperar a distância superior ao baseline."
    )
    return EfficiencyNarrative.model_validate(
        {
            "period": context.get("periodo", "diario"),
            "title": "Relatório de eficiência das rotas",
            "executive_summary": (
                f"O plano utiliza {metrics['veiculos_utilizados']} veículos e "
                f"percorre {distance:.2f} km."
            ),
            "highlights": (
                f"Comparação realizada contra {comparison['abordagem']}.",
                f"Variação de distância: {distance_savings:.2f} km; de custo: "
                f"{cost_savings:.2f}; de tempo estimado: {time_savings:.2f} min.",
            ),
            "risks": ("Estimativas não consideram trânsito em tempo real.",),
            "suggested_improvements": (
                distance_pattern,
                "Comparar tempos estimados e realizados para calibrar a velocidade.",
            ),
            "metrics_interpretation": (
                f"Custo operacional estimado: {operating_cost:.2f}.",
                "Economias negativas indicam desempenho inferior ao baseline.",
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
