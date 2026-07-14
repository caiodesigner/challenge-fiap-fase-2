# Otimização de Rotas Médicas

Projeto do Tech Challenge — Fase 2 da FIAP para otimizar a distribuição de
medicamentos e insumos por meio de algoritmos genéticos e produzir instruções e
relatórios com apoio de LLMs.

O repositório contém uma solução executável com cenários sintéticos, algoritmo
genético, restrições operacionais, experimentos, mapas, integração com LLM e
interface web.

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

Ou execute todo o pipeline local:

```bash
make check
```

Para aplicar a formatação automaticamente:

```bash
python -m ruff format .
```

## Executar a aplicação

Instale o [Ollama](https://docs.ollama.com/quickstart) e baixe a LLM gratuita
uma vez:

```bash
ollama pull qwen2.5:1.5b
```

Depois execute:

```bash
python -m rotas_medicas.api
```

A interface estará disponível em `http://127.0.0.1:8000` e a documentação da
API em `http://127.0.0.1:8000/docs`.

Para validar somente o restante da aplicação sem inferência, use
`LLM_PROVIDER=local python -m rotas_medicas.api`.

## Vídeo de demonstração

A demonstração completa do sistema está disponível no YouTube:

- [Tech Challenge — Otimização de Rotas Médicas](https://youtu.be/hlAF68vhlQU)

## Entregáveis

- [Relatório técnico consolidado](docs/relatorio-tecnico.md)
- [Evolução do código-base de TSP](docs/evolucao-codigo-base.md)
- [Arquitetura da solução](docs/arquitetura.md)
- [Guia da API](docs/api.md)
- [Vídeo de demonstração](https://youtu.be/hlAF68vhlQU)
- [Roteiro do vídeo de demonstração](docs/roteiro-video.md)
- [Validação final antes do vídeo](docs/demonstracao-final.md)
- [Checklist de entrega](docs/checklist-entrega.md)
- [Implantação opcional no Google Cloud](docs/nuvem.md)
- [Índice completo da documentação](docs/indice.md)

## Estrutura

```text
src/rotas_medicas/
├── api/             # API FastAPI e interface web
├── application/     # Orquestração dos casos de uso
├── domain/          # Entidades e regras do domínio
├── genetic/         # Algoritmo genético e operadores
├── llm/             # Prompts, relatórios e perguntas
├── optimization/    # Fitness, validação e baselines
└── visualization/   # Mapas e gráficos

data/                # Dados de entrada e cenários de demonstração
docs/                # Especificações e arquitetura
scripts/             # Comandos operacionais reproduzíveis
tests/               # Testes automatizados
infra/terraform/     # Infraestrutura Google Cloud como código
```

## Documentação por etapa

- [Definição do problema e critérios](docs/definicao-do-problema.md)
- [Dados e cenários de demonstração](data/README.md)
- [Algoritmo genético](docs/algoritmo-genetico.md)
- [Evolução do código-base de TSP](docs/evolucao-codigo-base.md)
- [Fitness e restrições](docs/fitness-e-restricoes.md)
- [Baselines e experimentos](docs/baselines-e-experimentos.md)
- [Visualizações](docs/visualizacoes.md)
- [Integração com LLM](docs/integracao-llm.md)
- [Demonstração e avaliação da LLM](docs/demonstracao-final.md)
- [Interface da solução](docs/interface-da-solucao.md)
- [Testes e qualidade](docs/testes-e-qualidade.md)
- [Nuvem — opcional](docs/nuvem.md)
