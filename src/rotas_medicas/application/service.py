"""Orquestração dos casos de uso expostos pela interface."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from threading import Lock
from types import MappingProxyType
from typing import Literal
from uuid import uuid4

from rotas_medicas.domain import RoutingProblem, load_scenario
from rotas_medicas.genetic import (
    GeneticAlgorithm,
    GeneticConfig,
    GeneticResult,
    RouteChromosome,
)
from rotas_medicas.llm import (
    DriverInstructions,
    EfficiencyReport,
    LLMProvider,
    QualityAssessment,
    RouteAnswer,
    RouteLanguageService,
)
from rotas_medicas.optimization import (
    FeasibilityIssue,
    FitnessEvaluation,
    RoutingFitness,
    find_feasibility_issues,
)


class ScenarioNotFoundError(LookupError):
    """Indica que o cenário solicitado não pertence ao catálogo."""


class SolutionNotFoundError(LookupError):
    """Indica que a solução não existe no armazenamento desta instância."""


class InfeasibleScenarioError(ValueError):
    """Contém os diagnósticos que impediram executar a otimização."""

    def __init__(self, issues: tuple[FeasibilityIssue, ...]) -> None:
        super().__init__("O cenário possui inviabilidades detectáveis.")
        self.issues = issues


class OptimizationFailedError(RuntimeError):
    """Indica que o algoritmo terminou sem um plano final executável."""


@dataclass(frozen=True, slots=True)
class ScenarioSummary:
    """Metadados exibidos antes de carregar ou otimizar um cenário."""

    id: str
    name: str
    deliveries: int
    vehicles: int
    expected_feasible: bool
    detected_issues: tuple[FeasibilityIssue, ...]


@dataclass(frozen=True, slots=True)
class SolutionRecord:
    """Estado completo de uma otimização disponível para consultas posteriores."""

    id: str
    problem: RoutingProblem
    chromosome: RouteChromosome
    evaluation: FitnessEvaluation
    genetic_result: GeneticResult


class InMemorySolutionStore:
    """Armazenamento concorrente e efêmero adequado à demonstração local."""

    def __init__(self) -> None:
        self._records: dict[str, SolutionRecord] = {}
        self._lock = Lock()

    def save(self, record: SolutionRecord) -> None:
        """Salva uma solução de forma atômica."""
        with self._lock:
            self._records[record.id] = record

    def get(self, solution_id: str) -> SolutionRecord:
        """Retorna uma solução ou falha com erro de aplicação específico."""
        with self._lock:
            try:
                return self._records[solution_id]
            except KeyError as error:
                raise SolutionNotFoundError(solution_id) from error


class RouteApplicationService:
    """Fachada para catálogo, otimização e recursos de linguagem."""

    def __init__(
        self,
        data_dir: str | Path,
        llm_provider: LLMProvider,
        store: InMemorySolutionStore | None = None,
    ) -> None:
        self._llm_provider = llm_provider
        self._store = store or InMemorySolutionStore()
        paths = {
            path.stem.removeprefix("cenario_"): path
            for path in Path(data_dir).glob("cenario_*.json")
        }
        if not paths:
            raise ValueError("Nenhum cenário foi encontrado no diretório de dados.")
        self._scenario_paths: Mapping[str, Path] = MappingProxyType(paths)

    def list_scenarios(self) -> tuple[ScenarioSummary, ...]:
        """Lista cenários e diagnósticos sem executar o algoritmo genético."""
        summaries = []
        for scenario_id in sorted(self._scenario_paths):
            problem = load_scenario(self._scenario_paths[scenario_id])
            summaries.append(
                ScenarioSummary(
                    id=scenario_id,
                    name=problem.metadata.name,
                    deliveries=len(problem.deliveries),
                    vehicles=len(problem.vehicles),
                    expected_feasible=problem.metadata.expected_feasible,
                    detected_issues=find_feasibility_issues(problem),
                )
            )
        return tuple(summaries)

    def optimize(
        self,
        scenario_id: str,
        config: GeneticConfig,
    ) -> SolutionRecord:
        """Valida, otimiza e armazena um cenário."""
        problem = self._load_problem(scenario_id)
        issues = find_feasibility_issues(problem)
        if issues:
            raise InfeasibleScenarioError(issues)
        effective_config = replace(
            config,
            seed=config.seed if config.seed is not None else problem.metadata.seed,
        )
        fitness = RoutingFitness(problem)
        result = GeneticAlgorithm(effective_config).run(
            problem.delivery_ids,
            len(problem.vehicles),
            fitness,
        )
        evaluation = fitness.evaluate(result.best_chromosome)
        if not evaluation.feasible:
            raise OptimizationFailedError(
                "O algoritmo não encontrou um plano executável com esta configuração."
            )
        record = SolutionRecord(
            id=str(uuid4()),
            problem=problem,
            chromosome=result.best_chromosome,
            evaluation=evaluation,
            genetic_result=result,
        )
        self._store.save(record)
        return record

    def get_solution(self, solution_id: str) -> SolutionRecord:
        """Consulta uma solução criada nesta instância da aplicação."""
        return self._store.get(solution_id)

    def generate_instructions(
        self,
        solution_id: str,
    ) -> tuple[DriverInstructions, QualityAssessment]:
        """Gera instruções fundamentadas na solução armazenada."""
        return self._language_service(solution_id).generate_driver_instructions()

    def generate_report(
        self,
        solution_id: str,
        period: Literal["diario", "semanal"],
    ) -> EfficiencyReport:
        """Gera um relatório operacional para o período solicitado."""
        return self._language_service(solution_id).generate_efficiency_report(period)

    def answer_question(
        self,
        solution_id: str,
        question: str,
    ) -> tuple[RouteAnswer, QualityAssessment]:
        """Responde a uma pergunta sobre uma solução específica."""
        return self._language_service(solution_id).answer_question(question)

    def _load_problem(self, scenario_id: str) -> RoutingProblem:
        try:
            path = self._scenario_paths[scenario_id]
        except KeyError as error:
            raise ScenarioNotFoundError(scenario_id) from error
        return load_scenario(path)

    def _language_service(self, solution_id: str) -> RouteLanguageService:
        record = self._store.get(solution_id)
        return RouteLanguageService(
            record.problem,
            record.chromosome,
            record.evaluation,
            self._llm_provider,
        )
