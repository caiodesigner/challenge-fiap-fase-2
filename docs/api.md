# Documentação da API

## Acesso

Inicie a aplicação:

```bash
python -m rotas_medicas.api
```

Base local: `http://127.0.0.1:8000`.

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
- Health check: `/health`

Os exemplos abaixo usam o provedor LLM local padrão e não exigem chave.

## Listar cenários

```http
GET /api/scenarios
```

Resposta resumida:

```json
[
  {
    "id": "pequeno",
    "name": "Cenário pequeno",
    "deliveries": 8,
    "vehicles": 2,
    "expected_feasible": true,
    "detected_issues": []
  }
]
```

Cenários com `detected_issues` não devem ser enviados para otimização.

## Otimizar

```http
POST /api/optimize
Content-Type: application/json
```

```json
{
  "scenario_id": "pequeno",
  "population_size": 60,
  "max_generations": 120,
  "crossover_rate": 0.9,
  "mutation_rate": 0.25,
  "elite_count": 3,
  "tournament_size": 4,
  "stagnation_generations": 40,
  "seed": 101
}
```

Campos omitidos recebem os padrões mostrados. A resposta contém:

- `solution_id`: UUID efêmero;
- `metrics`: fitness, distância, custos, veículos e parada;
- `routes`: paradas e utilização por veículo;
- `geojson`: dados prontos para o mapa;
- `best_cost_history`: convergência por geração.

Exemplo com cURL:

```bash
curl -X POST http://127.0.0.1:8000/api/optimize \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"pequeno","seed":101}'
```

## Recuperar solução

```http
GET /api/solutions/{solution_id}
```

O UUID só existe enquanto o processo atual estiver em execução.

## Gerar instruções

```http
POST /api/solutions/{solution_id}/instructions
Content-Type: application/json
```

Corpo: `{}`.

A resposta contém `content` estruturado por veículo e `quality`, com pontuação,
validade e problemas detectados.

## Gerar relatório

```http
POST /api/solutions/{solution_id}/report
Content-Type: application/json
```

```json
{
  "period": "diario"
}
```

`period` aceita `diario` ou `semanal`.

## Perguntar sobre a rota

```http
POST /api/solutions/{solution_id}/question
Content-Type: application/json
```

```json
{
  "question": "Quais veículos participam do plano?"
}
```

A resposta traz IDs de evidência. IDs inventados pelo provedor são rejeitados
antes de chegar ao cliente.

## Códigos de resposta

| Código | Significado |
|---:|---|
| 200 | Operação concluída |
| 404 | Cenário ou solução inexistente |
| 422 | Corpo inválido, cenário inviável ou otimização sem solução executável |
| 500 | Falha não tratada de infraestrutura ou provedor |

No cenário inviável, o corpo 422 contém uma lista `issues` com código e mensagem.

## Limites da requisição de otimização

| Campo | Mínimo | Máximo |
|---|---:|---:|
| `population_size` | 10 | 300 |
| `max_generations` | 1 | 1.000 |
| `crossover_rate` | 0 | 1 |
| `mutation_rate` | 0 | 1 |
| `elite_count` | 1 | 50 |
| `tournament_size` | 2 | 50 |
| `stagnation_generations` | 1 | 1.000 |

Combinações relacionais inválidas, como elitismo maior que a população, também
são rejeitadas.

## Configuração da LLM

Fallback determinístico:

```bash
export LLM_PROVIDER=local
```

Ollama com LLM pré-treinada:

```bash
ollama pull qwen2.5:1.5b
export LLM_PROVIDER=ollama
export OLLAMA_MODEL="qwen2.5:1.5b"
```

O Ollama executa localmente e não exige chave de API.
