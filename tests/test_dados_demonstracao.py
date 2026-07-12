"""Validações dos cenários sintéticos versionados."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

PASTA_DADOS = Path(__file__).resolve().parents[1] / "data"
ARQUIVOS_ESPERADOS = {
    "cenario_pequeno.json": (8, 2, True),
    "cenario_medio.json": (30, 5, True),
    "cenario_critico.json": (18, 3, True),
    "cenario_inviavel.json": (6, 2, False),
}
PRIORIDADES = {"critica", "alta", "normal", "baixa"}
TIPOS_DESTINO = {"unidade_saude", "atendimento_domiciliar"}


def carregar_cenario(nome: str) -> dict[str, Any]:
    """Carrega um arquivo de cenário como objeto JSON."""
    return json.loads((PASTA_DADOS / nome).read_text(encoding="utf-8"))


def test_cenarios_obedecem_ao_schema_json() -> None:
    """Todos os cenários versionados devem cumprir o contrato formal."""
    schema = json.loads(
        (PASTA_DADOS / "schema" / "cenario.schema.json").read_text(encoding="utf-8")
    )
    validador = jsonschema.Draft202012Validator(schema)

    for nome in ARQUIVOS_ESPERADOS:
        erros = sorted(validador.iter_errors(carregar_cenario(nome)), key=str)
        assert erros == []


def test_cenarios_esperados_existem_e_possuem_dimensoes_corretas() -> None:
    """A coleção deve cobrir os quatro níveis planejados."""
    arquivos = {arquivo.name for arquivo in PASTA_DADOS.glob("cenario_*.json")}
    assert arquivos == set(ARQUIVOS_ESPERADOS)

    for nome, (
        quantidade_entregas,
        quantidade_veiculos,
        viavel,
    ) in ARQUIVOS_ESPERADOS.items():
        dados = carregar_cenario(nome)
        assert len(dados["entregas"]) == quantidade_entregas
        assert len(dados["veiculos"]) == quantidade_veiculos
        assert dados["cenario"]["viavel_esperado"] is viavel


def test_identificadores_e_valores_sao_validos() -> None:
    """IDs devem ser únicos e valores operacionais devem ser positivos."""
    for nome in ARQUIVOS_ESPERADOS:
        dados = carregar_cenario(nome)
        entregas = dados["entregas"]
        veiculos = dados["veiculos"]

        assert len({item["id"] for item in entregas}) == len(entregas)
        assert len({item["id"] for item in veiculos}) == len(veiculos)
        assert all(item["demanda"] > 0 for item in entregas)
        assert all(item["prioridade"] in PRIORIDADES for item in entregas)
        assert all(item["tipo_destino"] in TIPOS_DESTINO for item in entregas)
        assert all(-90 <= item["latitude"] <= 90 for item in entregas)
        assert all(-180 <= item["longitude"] <= 180 for item in entregas)
        assert all(item["capacidade"] > 0 for item in veiculos)
        assert all(item["autonomia_km"] > 0 for item in veiculos)


def test_cenarios_viaveis_tem_capacidade_agregada_suficiente() -> None:
    """Cenários viáveis não podem falhar em verificações básicas de carga."""
    for nome in ARQUIVOS_ESPERADOS:
        dados = carregar_cenario(nome)
        if not dados["cenario"]["viavel_esperado"]:
            continue

        capacidades = [
            item["capacidade"] for item in dados["veiculos"] if item["disponivel"]
        ]
        demandas = [item["demanda"] for item in dados["entregas"]]
        assert sum(demandas) <= sum(capacidades)
        assert max(demandas) <= max(capacidades)


def test_cenario_inviavel_documenta_e_contem_a_causa() -> None:
    """O cenário negativo deve ser impossível pela causa documentada."""
    dados = carregar_cenario("cenario_inviavel.json")
    maior_capacidade = max(item["capacidade"] for item in dados["veiculos"])
    entregas_excessivas = [
        item for item in dados["entregas"] if item["demanda"] > maior_capacidade
    ]

    assert dados["cenario"]["motivo_inviabilidade_esperado"]
    assert [item["id"] for item in entregas_excessivas] == ["ENT-001"]
