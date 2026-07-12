# Roteiro do vídeo de demonstração

Duração máxima do enunciado: 15 minutos. Meta deste roteiro: 13 a 14 minutos,
preservando margem para transições.

## Preparação antes de gravar

- Ativar o ambiente e executar `make check`.
- Iniciar `python -m rotas_medicas.api`.
- Confirmar `http://127.0.0.1:8000/health`.
- Abrir a interface e `/docs` em abas separadas.
- Usar o cenário pequeno primeiro e o médio para resultados.
- Decidir entre provedor LLM local ou OpenAI.
- Se usar OpenAI, testar a chave antes e não exibir terminal com segredo.
- Fechar notificações e aumentar zoom do navegador.
- Ter o relatório e as visualizações previamente abertos.

## 0:00–0:45 — Abertura

Fala sugerida:

> Este é o Projeto 2 da Fase 2: otimização de rotas para distribuição de
> medicamentos e insumos. A solução usa algoritmo genético para um problema de
> múltiplos veículos e uma LLM para apresentar instruções e relatórios.

Mostrar:

- título do repositório;
- objetivo em uma frase;
- ausência de dados pessoais: todos os cenários são sintéticos.

## 0:45–2:00 — Problema e restrições

Explicar:

- depósito central;
- unidades de saúde e atendimentos domiciliares;
- prioridades diferentes;
- capacidade e autonomia;
- múltiplos veículos;
- objetivo composto, não apenas menor distância.

Mostrar o cenário pequeno na interface ou o JSON resumidamente.

## 2:00–3:15 — Arquitetura

Abrir [Arquitetura](arquitetura.md) e mostrar o diagrama de componentes.

Destacar:

- API e aplicação orquestram;
- domínio é independente;
- algoritmo genético recebe fitness;
- visualização consome solução pronta;
- LLM não calcula nem altera rota.

## 3:15–5:15 — Algoritmo genético

Abrir [Evolução do código-base](evolucao-codigo-base.md) e mostrar rapidamente
os módulos `genetic`.

Explicar:

- o código-base partia de permutação única, distância euclidiana, OX, mutação e
  elitismo;
- esses conceitos foram preservados e refatorados de TSP para VRP médico;
- cromossomo como lista de rotas por veículo;
- população inicial por seed;
- seleção por torneio e elitismo;
- crossover OX;
- mutações de troca, inversão e realocação;
- critérios de parada.

Evitar navegar linha por linha. Usar um exemplo simples de cromossomo.

## 5:15–6:30 — Fitness

Mostrar a decomposição no relatório técnico.

Destacar:

- distância;
- custo operacional;
- prioridade e atraso;
- veículos utilizados;
- penalidades dominantes para capacidade e autonomia.

Explicar que uma rota curta, porém impossível, não pode vencer.

## 6:30–8:30 — Demonstração da interface

Na interface:

1. selecionar cenário pequeno;
2. manter seed 101;
3. executar otimização;
4. mostrar fitness, distância, custo e veículos;
5. abrir marcadores do mapa;
6. mostrar carga e autonomia por rota.

Se o tempo permitir, mostrar que o cenário inviável aparece desabilitado.

## 8:30–10:00 — Experimentos e comparação

Abrir [Resultados iniciais](../reports/experiments/resultados-iniciais.md).

Apresentar:

- três baselines;
- três configurações genéticas;
- três seeds;
- 24 execuções viáveis;
- redução de 25,85% no pequeno;
- redução de 27,75% no médio;
- melhor execução individual do médio: balanceada, seed 11.

Abrir [Convergência do médio](../reports/visualizations/medio.convergencia.svg).

Explicar que menor distância isolada não implica melhor fitness, pois prioridade
e custo também importam.

## 10:00–11:45 — Integração com LLM

Na interface, usar a solução já calculada:

1. clicar em gerar instruções;
2. mostrar estrutura por veículo e parada;
3. gerar relatório;
4. perguntar quais veículos participam.

Falar explicitamente qual provedor está ativo:

- local: demonstração determinística sem LLM externa;
- OpenAI: Responses API com Structured Outputs.

Explicar as proteções:

- sequência não pode mudar;
- IDs inventados são rejeitados;
- sem diagnóstico ou prescrição;
- apenas dados estruturados do plano.

Para atender plenamente à demonstração de LLM do enunciado, prefira gravar esta
parte com `LLM_PROVIDER=openai`, após validação institucional da chave e custos.

## 11:45–12:45 — API e testes

Abrir `/docs` e mostrar os endpoints sem executar todos.

Mostrar terminal com resultado de `make check`:

- 110 testes;
- 94,22% de cobertura;
- Ruff;
- mypy estrito;
- pipeline GitHub Actions.

## 12:45–13:30 — Limitações e conclusão

Mencionar objetivamente:

- Haversine, sem ruas e trânsito real;
- armazenamento em memória;
- dados sintéticos;
- configuração de nuvem implementada, com provisionamento externo pendente.

Fechar reforçando:

> O algoritmo decide e valida as rotas; a LLM traduz a solução para comunicação
> operacional, mantendo decisões auditáveis.

## Checklist pós-gravação

- Confirmar duração menor ou igual a 15 minutos.
- Verificar legibilidade do terminal e navegador.
- Garantir que nenhum segredo apareceu.
- Conferir áudio e sincronização.
- Fazer upload público ou não listado no YouTube/Vimeo.
- Inserir o link no README e no checklist de entrega.
