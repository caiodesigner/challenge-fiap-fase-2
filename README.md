# Otimização de Rotas Médicas

Projeto do Tech Challenge — Fase 2 da FIAP para otimizar a distribuição de
medicamentos e insumos por meio de algoritmos genéticos e produzir instruções e
relatórios com apoio de LLMs.

O repositório contém a definição do problema, cenários sintéticos e o motor do
algoritmo genético. A função de fitness e as demais funcionalidades de negócio
serão incorporadas nas próximas etapas.

## Requisitos

- Python 3.12
- `venv` e `pip`

## Configuração local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

O uso de `python -m` evita executar acidentalmente ferramentas pertencentes a
outro ambiente Python.

## Verificações de desenvolvimento

Com o ambiente virtual ativado:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest
```

Para aplicar a formatação automaticamente:

```bash
python -m ruff format .
```

## Estrutura

```text
src/rotas_medicas/
├── api/             # Interfaces HTTP futuras
├── application/     # Orquestração dos casos de uso
├── domain/          # Entidades e regras do domínio
├── genetic/         # Algoritmo genético e operadores
├── llm/             # Prompts, relatórios e perguntas
├── optimization/    # Fitness, validação e baselines
└── visualization/   # Mapas e gráficos

data/                # Dados de entrada e cenários de demonstração
docs/                # Especificações e arquitetura
notebooks/           # Análises e demonstrações exploratórias
scripts/             # Comandos operacionais reproduzíveis
tests/               # Testes automatizados
```

## Documentação

- [Definição do problema e critérios](docs/definicao-do-problema.md)
- [Dados e cenários de demonstração](data/README.md)
- [Algoritmo genético](docs/algoritmo-genetico.md)
- [Fitness e restrições](docs/fitness-e-restricoes.md)
- [Baselines e experimentos](docs/baselines-e-experimentos.md)
- [Visualizações](docs/visualizacoes.md)
- [Integração com LLM](docs/integracao-llm.md)
