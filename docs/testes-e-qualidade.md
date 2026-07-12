# Testes e qualidade

## Estratégia

A suíte combina testes unitários, integração e HTTP. O objetivo é verificar não
apenas caminhos de sucesso, mas também invariantes, dados inválidos,
inviabilidades e respostas externas inconsistentes.

## Camadas cobertas

| Área | Exemplos de validação |
|---|---|
| Domínio | coordenadas, demanda, frota, IDs e prioridades |
| Algoritmo genético | representação, crossover, mutações e parada |
| Otimização | distância, fitness, penalidades e baselines |
| Experimentos | matriz de configurações, seeds e relatórios |
| Visualização | GeoJSON, HTML e SVG |
| LLM | contratos, fundamentação, sequência e API Ollama simulada |
| Aplicação | catálogo, armazenamento e orquestração |
| API | interface, OpenAPI, otimização, LLM e erros HTTP |

## Controles automáticos

### Ruff

Valida erros comuns, imports, modernização de Python, padrões de Pytest e
formatação consistente em 88 colunas.

### mypy

Executa em modo estrito sobre todo o pacote `rotas_medicas`. Fronteiras com JSON,
SDKs e FastAPI devem ser validadas ou convertidas explicitamente.

### Pytest e cobertura

A cobertura inclui branches e exige no mínimo 90%. O relatório no terminal
mostra linhas ausentes. No CI, também é criado `coverage.xml` como artefato por
sete dias.

### Verificação de dependências

`python -m pip check` confirma que as versões instaladas não possuem requisitos
incompatíveis.

## Pipeline local

```bash
make check
```

Comandos individuais:

```bash
make lint
make type
make test
```

## Integração contínua

O workflow `.github/workflows/quality.yml` é executado em pushes e pull requests
para `main`. Ele usa Python 3.12, cache do pip, permissões somente de leitura e
timeout de 15 minutos.

Etapas do job:

1. checkout;
2. instalação reproduzível do projeto;
3. integridade das dependências;
4. lint e formatação;
5. tipagem estática;
6. testes e cobertura;
7. upload do XML de cobertura.

Execuções concorrentes da mesma branch são canceladas quando uma versão mais
nova é enviada.

## Limitações

- O serviço real do Ollama não é chamado pelo CI.
- Tiles do OpenStreetMap não são carregados nos testes.
- Tempos de execução não são usados como asserção por variarem entre máquinas.
- Testes de carga, segurança dinâmica e navegador real ficam para uma evolução.
