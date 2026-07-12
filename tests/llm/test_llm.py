"""Testes de prompts, provedores, validação e casos de uso da LLM."""

from __future__ import annotations

import json

import httpx
import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.llm import (
    DriverGuidance,
    DriverInstructions,
    EfficiencyNarrative,
    LLMValidationError,
    OllamaProvider,
    QueueProvider,
    RouteAnswer,
    RouteLanguageService,
    RuleBasedProvider,
)
from rotas_medicas.llm.prompts import PROMPT_VERSION, SYSTEM_PROMPT, route_context
from rotas_medicas.llm.schemas import DeliveryStep, VehicleInstructions
from rotas_medicas.optimization import RoutingFitness, original_order


def plan(problem: RoutingProblem) -> tuple[RouteChromosome, RoutingFitness]:
    """Retorna um plano viável e sua fitness."""
    chromosome = original_order(problem)
    return chromosome, RoutingFitness(problem)


def valid_instructions(
    problem: RoutingProblem,
    chromosome: RouteChromosome,
) -> DriverInstructions:
    """Monta instruções perfeitamente alinhadas ao cromossomo."""
    deliveries = problem.deliveries_by_id
    routes = tuple(
        VehicleInstructions(
            vehicle_id=problem.vehicles[index].id,
            summary="Executar rota planejada.",
            steps=tuple(
                DeliveryStep(
                    stop=stop,
                    delivery_id=delivery_id,
                    destination=deliveries[delivery_id].destination,
                    priority=deliveries[delivery_id].priority.value,
                    instruction="Confirmar e registrar a entrega.",
                )
                for stop, delivery_id in enumerate(route, start=1)
            ),
        )
        for index, route in enumerate(chromosome.routes)
        if route
    )
    return DriverInstructions(
        title="Instruções",
        general_guidance=("Seguir a ordem.",),
        routes=routes,
    )


def valid_guidance() -> DriverGuidance:
    return DriverGuidance(
        operational_focus="conferencia_carga",
        critical_focus="confirmacao_recebimento",
        standard_focus="registro_entrega",
        alert_focus="comunicar_impedimento",
    )


def test_context_contains_only_calculated_route_facts(
    small_problem: RoutingProblem,
) -> None:
    """Contexto deve ser rastreável ao cenário e à avaliação."""
    chromosome, fitness = plan(small_problem)
    evaluation = fitness.evaluate(chromosome)

    context = route_context(small_problem, chromosome, evaluation)

    assert context["versao_prompt"] == PROMPT_VERSION
    assert context["metricas"]["plano_viavel"] is True
    assert context["comparacao_baseline"]["abordagem"]
    assert "economia_tempo_min" in context["comparacao_baseline"]
    assert context["rotas"][0]["paradas"][0]["entrega_id"] == "ENT-001"
    assert "Não altere nem recalcule" in SYSTEM_PROMPT


def test_service_generates_and_validates_all_use_cases(
    small_problem: RoutingProblem,
) -> None:
    """Instruções, relatório e resposta devem cumprir seus contratos."""
    chromosome, fitness = plan(small_problem)
    guidance = valid_guidance()
    report = EfficiencyNarrative(
        period="diario",
        title="Relatório",
        executive_summary="Plano viável.",
        highlights=("Rotas calculadas.",),
        risks=("Sem trânsito em tempo real.",),
        suggested_improvements=("Medir tempos reais.",),
        metrics_interpretation=("Distância calculada.",),
    )
    answer = RouteAnswer(
        answer="O veículo VEI-001 participa.",
        evidence_vehicle_ids=("VEI-001",),
    )
    provider = QueueProvider([guidance, report, answer])
    service = RouteLanguageService(
        small_problem,
        chromosome,
        fitness.evaluate(chromosome),
        provider,
    )

    generated_instructions, instruction_quality = service.generate_driver_instructions()
    generated_report = service.generate_efficiency_report()
    generated_answer, answer_quality = service.answer_question("Qual veículo?")

    assert generated_instructions.routes
    assert generated_instructions.title == "Instruções operacionais do plano otimizado"
    assert instruction_quality.score == 1
    assert generated_report.period == report.period
    assert generated_report.title == report.title
    assert generated_report.comparison.baseline_name
    assert generated_report.comparison.baseline_distance_km > 0
    assert generated_answer == answer
    assert answer_quality.valid
    assert len(provider.requests) == 3
    assert all("<dados_json>" in request[1] for request in provider.requests)


def test_llm_guidance_cannot_change_route(
    small_problem: RoutingProblem,
) -> None:
    """IDs e sequência devem vir do cromossomo, não da resposta da LLM."""
    chromosome, fitness = plan(small_problem)
    service = RouteLanguageService(
        small_problem,
        chromosome,
        fitness.evaluate(chromosome),
        QueueProvider([valid_guidance()]),
    )

    instructions, quality = service.generate_driver_instructions()

    assert quality.valid
    assert (
        tuple(step.delivery_id for route in instructions.routes for step in route.steps)
        == chromosome.delivery_ids
    )


def test_rejects_unknown_answer_evidence(small_problem: RoutingProblem) -> None:
    """Evidências inventadas devem bloquear a resposta."""
    chromosome, fitness = plan(small_problem)
    answer = RouteAnswer(
        answer="Entrega inexistente.",
        evidence_delivery_ids=("ENT-999",),
    )
    service = RouteLanguageService(
        small_problem,
        chromosome,
        fitness.evaluate(chromosome),
        QueueProvider([answer]),
    )

    with pytest.raises(LLMValidationError, match="Entregas desconhecidas"):
        service.answer_question("Qual entrega?")


def test_rule_based_provider_supports_offline_demonstration(
    small_problem: RoutingProblem,
) -> None:
    """O pipeline local deve funcionar sem rede ou chave de API."""
    chromosome, fitness = plan(small_problem)
    service = RouteLanguageService(
        small_problem,
        chromosome,
        fitness.evaluate(chromosome),
        RuleBasedProvider(),
    )

    instructions, quality = service.generate_driver_instructions()
    report = service.generate_efficiency_report("semanal")
    answer, _ = service.answer_question("Quais veículos?")

    assert quality.valid
    assert report.period == "semanal"
    assert report.comparison.baseline_name
    assert report.comparison.optimized_estimated_minutes > 0
    assert answer.caveat == "Resposta gerada sem uma LLM externa."
    assert instructions.routes


def test_ollama_provider_uses_chat_with_json_schema(
    small_problem: RoutingProblem,
) -> None:
    """O adaptador deve enviar o contrato Pydantic à API local de chat."""
    chromosome, _ = plan(small_problem)
    expected = valid_instructions(small_problem, chromosome)
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={"message": {"content": expected.model_dump_json()}},
        )

    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    provider = OllamaProvider(
        model="modelo-teste",
        client=client,
    )

    response = provider.generate(
        system_prompt="sistema",
        user_prompt="usuário",
        response_model=DriverInstructions,
    )

    assert response == expected
    assert provider.model == "modelo-teste"
    assert captured["model"] == "modelo-teste"
    assert captured["format"] == DriverInstructions.model_json_schema()
    assert captured["stream"] is False


def test_ollama_provider_rejects_empty_structured_response() -> None:
    """Ausência de conteúdo não pode parecer sucesso."""
    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"message": {"content": ""}})
        ),
    )
    provider = OllamaProvider(client=client)

    with pytest.raises(RuntimeError, match="conteúdo vazio"):
        provider.generate(
            system_prompt="sistema",
            user_prompt="usuário",
            response_model=DriverInstructions,
        )


def test_ollama_provider_explains_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    provider = OllamaProvider(client=client)

    with pytest.raises(RuntimeError, match="não está acessível"):
        provider.generate(
            system_prompt="sistema",
            user_prompt="usuário",
            response_model=DriverInstructions,
        )


def test_ollama_provider_explains_missing_model() -> None:
    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(404, json={"error": "model not found"})
        ),
    )
    provider = OllamaProvider(model="modelo-ausente", client=client)

    with pytest.raises(RuntimeError, match="ollama pull modelo-ausente"):
        provider.generate(
            system_prompt="sistema",
            user_prompt="usuário",
            response_model=DriverInstructions,
        )
