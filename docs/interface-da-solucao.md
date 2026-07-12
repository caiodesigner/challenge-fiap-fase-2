# Interface da solução

## Visão geral

A solução disponibiliza uma aplicação FastAPI com interface web responsiva e
documentação OpenAPI automática. A interface reúne os fluxos construídos nas
etapas anteriores:

- seleção de cenário;
- configuração do algoritmo genético;
- execução da otimização;
- mapa interativo das rotas;
- métricas gerais e por veículo;
- instruções aos motoristas;
- relatório operacional;
- perguntas em linguagem natural.

## Execução

Com o ambiente virtual ativado:

```bash
python -m rotas_medicas.api
```

Abrir no navegador:

- interface: `http://127.0.0.1:8000`;
- Swagger UI: `http://127.0.0.1:8000/docs`;
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`;
- verificação de saúde: `http://127.0.0.1:8000/health`.

O provedor padrão é o Ollama local. Baixe o modelo antes de iniciar a API:

```bash
ollama pull qwen2.5:1.5b
export LLM_PROVIDER=ollama
export OLLAMA_MODEL="qwen2.5:1.5b"
python -m rotas_medicas.api
```

## Endpoints

| Método | Caminho | Finalidade |
|---|---|---|
| `GET` | `/health` | Estado básico do processo |
| `GET` | `/api/scenarios` | Catálogo e inviabilidades detectadas |
| `POST` | `/api/optimize` | Executa e armazena uma otimização |
| `GET` | `/api/solutions/{id}` | Recupera solução da instância atual |
| `POST` | `/api/solutions/{id}/instructions` | Instruções por veículo |
| `POST` | `/api/solutions/{id}/report` | Relatório diário ou semanal |
| `POST` | `/api/solutions/{id}/question` | Pergunta sobre as rotas |

Os contratos completos, limites de campos e exemplos podem ser explorados pela
documentação Swagger gerada pelo FastAPI.

## Fluxo de otimização

1. A API valida tipos e limites dos parâmetros com Pydantic.
2. A camada de aplicação carrega somente um cenário pertencente ao catálogo.
3. Inviabilidades evidentes são verificadas antes da evolução.
4. O algoritmo genético recebe a configuração validada.
5. A fitness confirma que a melhor solução é executável.
6. A solução recebe um UUID e é armazenada em memória.
7. A API devolve métricas, rotas, GeoJSON e histórico de convergência.

## Interface web

A página é servida pelo próprio backend e não exige processo de frontend
separado. Ela usa Leaflet e OpenStreetMap para desenhar o GeoJSON devolvido pela
API. Cenários com inviabilidades detectadas aparecem desabilitados na seleção.

A interface permite configurar população, gerações, mutação e seed. Outros
parâmetros continuam disponíveis diretamente pela API.

## Estado e concorrência

`InMemorySolutionStore` protege leituras e escritas com lock e mantém as
soluções apenas durante a vida do processo. Reiniciar o servidor apaga os UUIDs
anteriores. Persistência em banco de dados pertence a uma evolução futura.

A otimização é executada dentro da requisição. Isso simplifica a demonstração,
mas execuções grandes devem ser movidas para uma fila de tarefas antes de uma
implantação com múltiplos usuários.

## Segurança e limites atuais

- o catálogo impede acesso arbitrário a arquivos pelo `scenario_id`;
- corpos desconhecidos são rejeitados;
- população e gerações possuem limites máximos;
- cenários inviáveis retornam HTTP 422 com diagnóstico;
- IDs de solução inexistentes retornam HTTP 404;
- nenhuma chave ou credencial é necessária para o Ollama local;
- o modo local é usado por padrão.

Esta versão não possui autenticação, autorização, limitação de requisições ou
persistência. Por isso, deve ser tratada como aplicação acadêmica de
demonstração, não como sistema hospitalar pronto para produção.

## Testes HTTP

Os testes usam o transporte ASGI do HTTPX, sem abrir porta e sem acessar rede.
Eles cobrem interface, saúde, OpenAPI, catálogo, otimização, recuperação da
solução, ações de LLM e respostas de erro.
