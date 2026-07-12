"""Teste do ponto de entrada do servidor local."""

from typing import Any

import pytest

from rotas_medicas.api.__main__ import main
from rotas_medicas.api.app import data_dir_from_environment


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


def test_main_honors_cloud_run_network_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O contêiner deve respeitar host e porta injetados pelo ambiente."""
    captured: dict[str, Any] = {}

    def fake_run(app: str, **kwargs: object) -> None:
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setattr("rotas_medicas.api.__main__.uvicorn.run", fake_run)

    main()

    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8080


def test_data_directory_can_be_injected_by_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_DIR", "/app/data")

    assert str(data_dir_from_environment()) == "/app/data"
