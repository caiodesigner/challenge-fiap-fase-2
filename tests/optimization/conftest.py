"""Fixtures compartilhadas pelos testes de otimização."""

from pathlib import Path

import pytest

from rotas_medicas.domain import RoutingProblem, load_scenario

DATA_PATH = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def small_problem() -> RoutingProblem:
    """Carrega o cenário pequeno validado e versionado."""
    return load_scenario(DATA_PATH / "cenario_pequeno.json")
