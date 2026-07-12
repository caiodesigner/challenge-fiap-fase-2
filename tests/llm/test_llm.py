"""Testes de prompts, provedores, validação e casos de uso da LLM."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from rotas_medicas.domain import RoutingProblem
from rotas_medicas.genetic import RouteChromosome
from rotas_medicas.llm import (
    DriverInstructions,
    EfficiencyReport,
    LLMValidationError,
    OpenAIResponsesProvider,
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


def test_context_contains_only_calculated_route_facts(
    small_problem: RoutingProblem,
) -> None:
    """Contexto deve ser rastreável ao cenário e à avaliação."""
    chromosome, fitness = plan(small_problem)
    evaluation = fitness.evaluate(chromosome)

    context = route_context(small_problem, chromosome, evaluation)

    assert context["versao_prompt"] == PROMPT_VERSION
    assert context["metricas"]["plano_viavel"] is True
    assert context["rotas"][0]["paradas"][0]["entrega_id"] == "ENT-001"
    assert "Não altere nem recalcule" in SYSTEM_PROMPT


def test_service_generates_and_validates_all_use_cases(
    small_problem: RoutingProblem,
) -> None:
    """Instruções, relatório e resposta devem cumprir seus contratos."""
    chromosome, fitness = plan(small_problem)
    instructions = valid_instructions(small_problem, chromosome)
    report = EfficiencyReport(
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
    provider = QueueProvider([instructions, report, answer])
    service = RouteLanguageService(
        small_problem,
        chromosome,
        fitness.evaluate(chromosome),
        provider,
    )

    generated_instructions, instruction_quality = service.generate_driver_instructions()
    generated_report = service.generate_efficiency_report()
    generated_answer, answer_quality = service.answer_question("Qual veículo?")

    assert generated_instructions == instructions
    assert instruction_quality.score == 1
    assert generated_report == report
    assert generated_answer == answer
    assert answer_quality.valid
    assert len(provider.requests) == 3
    assert all("<dados_json>" in request[1] for request in provider.requests)


def test_rejects_instructions_that_change_route(
    small_problem: RoutingProblem,
) -> None:
    """A LLM não pode trocar a sequência calculada pelo otimizador."""
    chromosome, fitness = plan(small_problem)
    instructions = valid_instructions(small_problem, chromosome)
    first_route = instructions.routes[0]
    invalid_route = first_route.model_copy(
        update={"steps": tuple(reversed(first_route.steps))}
    )
    invalid = instructions.model_copy(
        update={"routes": (invalid_route, *instructions.routes[1:])}
    )
    service = RouteLanguageService(
        small_problem,
        chromosome,
        fitness.evaluate(chromosome),
        QueueProvider([invalid]),
    )

    with pytest.raises(LLMValidationError, match="Sequência divergente"):
        service.generate_driver_instructions()


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
    assert answer.caveat == "Resposta gerada sem uma LLM externa."
    assert instructions.routes


@dataclass
class FakeResponse:
    """Resposta mínima compatível com o adaptador OpenAI."""

    output_parsed: DriverInstructions | None


class FakeResponses:
    """Captura a chamada feita ao endpoint Responses."""

    def __init__(self, parsed: DriverInstructions | None) -> None:
        self.parsed = parsed
        self.kwargs: dict[str, object] = {}

    def parse(self, **kwargs: object) -> FakeResponse:
        """Registra os argumentos e devolve o objeto tipado."""
        self.kwargs = kwargs
        return FakeResponse(self.parsed)


class FakeOpenAI:
    """Cliente mínimo para não acessar a rede durante os testes."""

    def __init__(self, parsed: DriverInstructions | None) -> None:
        self.responses = FakeResponses(parsed)


def test_openai_provider_uses_responses_parse(
    small_problem: RoutingProblem,
) -> None:
    """O adaptador deve usar Structured Outputs com o modelo configurado."""
    chromosome, _ = plan(small_problem)
    expected = valid_instructions(small_problem, chromosome)
    client = FakeOpenAI(expected)
    provider = OpenAIResponsesProvider(
        model="modelo-teste",
        client=client,  # type: ignore[arg-type]
    )

    response = provider.generate(
        system_prompt="sistema",
        user_prompt="usuário",
        response_model=DriverInstructions,
    )

    assert response == expected
    assert provider.model == "modelo-teste"
    assert client.responses.kwargs["text_format"] is DriverInstructions
    assert client.responses.kwargs["model"] == "modelo-teste"


def test_openai_provider_rejects_empty_structured_response() -> None:
    """Recusa ou ausência de conteúdo não pode parecer sucesso."""
    provider = OpenAIResponsesProvider(
        client=FakeOpenAI(None),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="não retornou"):
        provider.generate(
            system_prompt="sistema",
            user_prompt="usuário",
            response_model=DriverInstructions,
        )
