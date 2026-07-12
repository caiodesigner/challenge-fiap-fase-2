"""Testes da fundação do pacote."""

import rotas_medicas


def test_package_exposes_version() -> None:
    """O pacote deve expor uma versão semântica inicial."""
    assert rotas_medicas.__version__ == "0.1.0"
