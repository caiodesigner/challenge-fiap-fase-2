"""Teste do ponto de entrada do servidor local."""

from typing import Any

import pytest

from rotas_medicas.api.__main__ import main


def test_main_starts_uvicorn_with_local_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O comando documentado deve iniciar a aplicação na porta esperada."""
    captured: dict[str, Any] = {}

    def fake_run(app: str, **kwargs: object) -> None:
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setattr("rotas_medicas.api.__main__.uvicorn.run", fake_run)

    main()

    assert captured == {
        "app": "rotas_medicas.api.app:app",
        "host": "127.0.0.1",
        "port": 8000,
        "reload": False,
    }
