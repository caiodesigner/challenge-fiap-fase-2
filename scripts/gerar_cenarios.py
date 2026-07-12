"""Gera cenários sintéticos e determinísticos para demonstração."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ / "data"
DATA_PLANEJAMENTO = "2026-08-03"
LATITUDE_DEPOSITO = -23.55052
LONGITUDE_DEPOSITO = -46.633308
PRIORIDADES = ("critica", "alta", "normal", "baixa")
CARGAS = (
    "Medicamentos de uso hospitalar",
    "Kits de curativo",
    "Soluções intravenosas",
    "Materiais descartáveis",
    "Insumos de laboratório",
)


def deposito() -> dict[str, Any]:
    """Retorna o depósito fictício compartilhado pelos cenários."""
    return {
        "id": "DEP-001",
        "nome": "Centro de Distribuição Hospitalar Central",
        "latitude": LATITUDE_DEPOSITO,
        "longitude": LONGITUDE_DEPOSITO,
    }


def configuracao() -> dict[str, Any]:
    """Retorna convenções comuns de distância, carga e prioridade."""
    return {
        "metodo_distancia": "haversine",
        "unidade_distancia": "km",
        "unidade_carga": "volume_logistico",
        "pesos_prioridade": {
            "critica": 4,
            "alta": 3,
            "normal": 2,
            "baixa": 1,
        },
    }


def veiculo(
    indice: int,
    capacidade: float,
    autonomia_km: float,
    custo_fixo: float,
    custo_por_km: float,
) -> dict[str, Any]:
    """Cria um veículo fictício da frota."""
    return {
        "id": f"VEI-{indice:03d}",
        "descricao": f"Veículo de distribuição {indice:02d}",
        "capacidade": capacidade,
        "autonomia_km": autonomia_km,
        "custo_fixo": custo_fixo,
        "custo_por_km": custo_por_km,
        "disponivel": True,
    }


def entrega(
    indice: int,
    latitude: float,
    longitude: float,
    demanda: float,
    prioridade: str,
    prazo_alvo_minutos: int | None,
) -> dict[str, Any]:
    """Cria uma entrega sem dados pessoais ou clínicos reais."""
    domiciliar = indice % 3 == 0
    prefixo = "Domicílio fictício" if domiciliar else "Unidade de saúde fictícia"
    return {
        "id": f"ENT-{indice:03d}",
        "destino": f"{prefixo} {indice:02d}",
        "tipo_destino": ("atendimento_domiciliar" if domiciliar else "unidade_saude"),
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "demanda": demanda,
        "prioridade": prioridade,
        "prazo_alvo_minutos": prazo_alvo_minutos,
        "descricao_carga": CARGAS[(indice - 1) % len(CARGAS)],
    }


def metadados(
    identificador: str,
    nome: str,
    descricao: str,
    seed: int,
    viavel: bool,
    motivo: str | None = None,
) -> dict[str, Any]:
    """Cria os metadados rastreáveis de um cenário."""
    return {
        "id": identificador,
        "nome": nome,
        "descricao": descricao,
        "data_planejamento": DATA_PLANEJAMENTO,
        "seed": seed,
        "viavel_esperado": viavel,
        "motivo_inviabilidade_esperado": motivo,
    }


def montar_cenario(
    metadado: dict[str, Any],
    veiculos: list[dict[str, Any]],
    entregas: list[dict[str, Any]],
) -> dict[str, Any]:
    """Monta a estrutura versionada comum a todos os arquivos."""
    return {
        "versao_schema": "1.0",
        "cenario": metadado,
        "configuracao": configuracao(),
        "deposito": deposito(),
        "veiculos": veiculos,
        "entregas": entregas,
    }


def criar_entregas(
    quantidade: int,
    seed: int,
    raio_graus: float,
    demandas: tuple[int, ...],
    prioridades: tuple[str, ...] = PRIORIDADES,
) -> list[dict[str, Any]]:
    """Distribui entregas em torno do depósito de forma determinística."""
    gerador = random.Random(seed)
    resultado = []
    for indice in range(1, quantidade + 1):
        angulo = (2 * math.pi * indice / quantidade) + gerador.uniform(-0.2, 0.2)
        raio = raio_graus * gerador.uniform(0.35, 1.0)
        prioridade = prioridades[(indice - 1) % len(prioridades)]
        prazos = {"critica": 60, "alta": 120, "normal": 240, "baixa": None}
        resultado.append(
            entrega(
                indice=indice,
                latitude=LATITUDE_DEPOSITO + raio * math.sin(angulo),
                longitude=LONGITUDE_DEPOSITO + raio * math.cos(angulo),
                demanda=demandas[(indice - 1) % len(demandas)],
                prioridade=prioridade,
                prazo_alvo_minutos=prazos[prioridade],
            )
        )
    return resultado


def cenario_pequeno() -> dict[str, Any]:
    """Cria um cenário simples para inspeção manual."""
    seed = 101
    return montar_cenario(
        metadados(
            "pequeno",
            "Cenário pequeno",
            "Validação manual das regras com oito entregas próximas.",
            seed,
            True,
        ),
        [
            veiculo(1, 35, 40, 75, 2.1),
            veiculo(2, 30, 35, 65, 1.9),
        ],
        criar_entregas(8, seed, 0.025, (5, 7, 4, 6)),
    )


def cenario_medio() -> dict[str, Any]:
    """Cria um cenário para comparação de desempenho e estabilidade."""
    seed = 202
    return montar_cenario(
        metadados(
            "medio",
            "Cenário médio",
            "Comparação de algoritmos com trinta entregas variadas.",
            seed,
            True,
        ),
        [
            veiculo(1, 65, 85, 110, 2.4),
            veiculo(2, 60, 80, 105, 2.3),
            veiculo(3, 55, 75, 95, 2.2),
            veiculo(4, 50, 70, 90, 2.0),
            veiculo(5, 45, 65, 80, 1.8),
        ],
        criar_entregas(30, seed, 0.065, (6, 8, 5, 10, 7)),
    )


def cenario_critico() -> dict[str, Any]:
    """Cria um cenário viável com pouca folga de carga e autonomia."""
    seed = 303
    prioridades = (
        "critica",
        "alta",
        "critica",
        "normal",
        "alta",
        "critica",
    )
    return montar_cenario(
        metadados(
            "critico",
            "Cenário crítico",
            "Alta demanda, entregas urgentes e frota com pouca folga.",
            seed,
            True,
        ),
        [
            veiculo(1, 55, 38, 100, 2.4),
            veiculo(2, 50, 36, 95, 2.3),
            veiculo(3, 45, 34, 85, 2.1),
        ],
        criar_entregas(18, seed, 0.035, (8, 9, 7, 10, 6, 9), prioridades),
    )


def cenario_inviavel() -> dict[str, Any]:
    """Cria um cenário cuja entrega maior não cabe em nenhum veículo."""
    seed = 404
    entregas = criar_entregas(6, seed, 0.02, (5, 7, 6, 8, 4, 5))
    entregas[0]["demanda"] = 60
    entregas[0]["descricao_carga"] = "Lote indivisível de soluções intravenosas"
    return montar_cenario(
        metadados(
            "inviavel",
            "Cenário inviável",
            "Validação da detecção de uma entrega indivisível excessiva.",
            seed,
            False,
            "A entrega ENT-001 excede a capacidade de todos os veículos.",
        ),
        [
            veiculo(1, 40, 40, 80, 2.0),
            veiculo(2, 35, 35, 70, 1.8),
        ],
        entregas,
    )


def main() -> None:
    """Grava todos os cenários com ordenação e formatação estáveis."""
    cenarios = {
        "cenario_pequeno.json": cenario_pequeno(),
        "cenario_medio.json": cenario_medio(),
        "cenario_critico.json": cenario_critico(),
        "cenario_inviavel.json": cenario_inviavel(),
    }
    for nome_arquivo, conteudo in cenarios.items():
        destino = PASTA_DADOS / nome_arquivo
        destino.write_text(
            json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Gerado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
