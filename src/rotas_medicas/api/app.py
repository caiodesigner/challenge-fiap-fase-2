"""Aplicação FastAPI e tratamento dos erros da camada de aplicação."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from rotas_medicas.api.schemas import (
    AnswerResponse,
    InstructionsResponse,
    OptimizationRequest,
    QualityResponse,
    QuestionRequest,
    ReportRequest,
    ReportResponse,
    ScenarioResponse,
    SolutionResponse,
)
from rotas_medicas.api.ui import INDEX_HTML
from rotas_medicas.application import (
    InfeasibleScenarioError,
    OptimizationFailedError,
    RouteApplicationService,
    ScenarioNotFoundError,
    SolutionNotFoundError,
)
from rotas_medicas.genetic import GeneticConfig
from rotas_medicas.llm import LLMProvider, OpenAIResponsesProvider, RuleBasedProvider


def data_dir_from_environment() -> Path:
    """Resolve cenários empacotados ou montados no ambiente de execução."""
    return Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[3] / "data"))


DEFAULT_DATA_DIR = data_dir_from_environment()


def _provider_from_environment() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "local").lower()
    if provider_name == "local":
        return RuleBasedProvider()
    if provider_name == "openai":
        return OpenAIResponsesProvider()
    raise ValueError("LLM_PROVIDER deve ser 'local' ou 'openai'.")


def create_app(
    service: RouteApplicationService | None = None,
    data_dir: str | Path = DEFAULT_DATA_DIR,
    llm_provider: LLMProvider | None = None,
) -> FastAPI:
    """Cria uma instância configurável para produção ou testes."""
    application_service = service or RouteApplicationService(
        data_dir,
        llm_provider or _provider_from_environment(),
    )
    app = FastAPI(
        title="Otimização de Rotas Médicas",
        version="0.1.0",
        description="Algoritmo genético, visualização e assistência por LLM.",
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index() -> str:
        return INDEX_HTML

    @app.get("/health", tags=["sistema"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(
        "/api/scenarios",
        response_model=tuple[ScenarioResponse, ...],
        tags=["cenários"],
    )
    async def list_scenarios() -> tuple[ScenarioResponse, ...]:
        return tuple(
            ScenarioResponse.from_summary(summary)
            for summary in application_service.list_scenarios()
        )

    @app.post(
        "/api/optimize",
        response_model=SolutionResponse,
        tags=["otimização"],
    )
    async def optimize(request: OptimizationRequest) -> SolutionResponse:
        try:
            config = GeneticConfig(
                population_size=request.population_size,
                max_generations=request.max_generations,
                crossover_rate=request.crossover_rate,
                mutation_rate=request.mutation_rate,
                elite_count=request.elite_count,
                tournament_size=request.tournament_size,
                stagnation_generations=request.stagnation_generations,
                seed=request.seed,
            )
            return SolutionResponse.from_record(
                application_service.optimize(request.scenario_id, config)
            )
        except ScenarioNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Cenário não encontrado."
            ) from error
        except InfeasibleScenarioError as error:
            detail = {
                "message": str(error),
                "issues": [
                    {"code": issue.code, "message": issue.message}
                    for issue in error.issues
                ],
            }
            raise HTTPException(status_code=422, detail=detail) from error
        except (OptimizationFailedError, ValueError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get(
        "/api/solutions/{solution_id}",
        response_model=SolutionResponse,
        tags=["soluções"],
    )
    async def get_solution(solution_id: str) -> SolutionResponse:
        try:
            return SolutionResponse.from_record(
                application_service.get_solution(solution_id)
            )
        except SolutionNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Solução não encontrada."
            ) from error

    @app.post(
        "/api/solutions/{solution_id}/instructions",
        response_model=InstructionsResponse,
        tags=["assistente"],
    )
    async def instructions(solution_id: str) -> InstructionsResponse:
        try:
            content, quality = application_service.generate_instructions(solution_id)
            return InstructionsResponse(
                content=content,
                quality=QualityResponse.from_assessment(quality),
            )
        except SolutionNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Solução não encontrada."
            ) from error

    @app.post(
        "/api/solutions/{solution_id}/report",
        response_model=ReportResponse,
        tags=["assistente"],
    )
    async def report(solution_id: str, request: ReportRequest) -> ReportResponse:
        try:
            return ReportResponse(
                content=application_service.generate_report(
                    solution_id,
                    request.period,
                )
            )
        except SolutionNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Solução não encontrada."
            ) from error

    @app.post(
        "/api/solutions/{solution_id}/question",
        response_model=AnswerResponse,
        tags=["assistente"],
    )
    async def question(solution_id: str, request: QuestionRequest) -> AnswerResponse:
        try:
            content, quality = application_service.answer_question(
                solution_id,
                request.question,
            )
            return AnswerResponse(
                content=content,
                quality=QualityResponse.from_assessment(quality),
            )
        except SolutionNotFoundError as error:
            raise HTTPException(
                status_code=404, detail="Solução não encontrada."
            ) from error

    return app


app = create_app()
