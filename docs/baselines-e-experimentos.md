# Baselines e experimentos

## Objetivo

Os experimentos comparam o algoritmo genético com heurísticas determinísticas e
avaliam como configurações distintas afetam qualidade, estabilidade e tempo de
execução. Todas as abordagens usam os mesmos cenários, matriz de distância e
função fitness.

## Baselines

### Ordem original

Percorre as entregas na ordem do arquivo e escolhe o primeiro veículo em que a
inserção no fim da rota respeite capacidade e autonomia. Representa um processo
operacional simples, sem otimização espacial ou de prioridade.

### Vizinho mais próximo

A cada passo, avalia todas as combinações viáveis entre a ponta das rotas e as
entregas ainda não atendidas. A combinação com menor distância é escolhida.

### Prioridade e distância

Ordena primeiro pelo peso da prioridade, depois pela distância ao depósito. Para
cada entrega, escolhe a rota viável com menor aumento de distância.

Caso nenhuma inserção seja viável, as heurísticas ainda preservam todas as
entregas e escolhem a atribuição com menor excesso estimado. A fitness registra
e penaliza essa violação, permitindo comparar cenários difíceis sem esconder
entregas.

## Configurações genéticas

Três perfis mantêm o mesmo tamanho de população e limite de gerações:

| Configuração | Crossover | Mutação | Elitismo | Torneio | Intenção |
|---|---:|---:|---:|---:|---|
| Exploração | 0,95 | 0,40 | 2 | 3 | Aumentar diversidade |
| Balanceada | 0,90 | 0,25 | 3 | 4 | Equilibrar busca e seleção |
| Explotação | 0,80 | 0,10 | 4 | 6 | Intensificar soluções promissoras |

O perfil `full` usa população 80, até 160 gerações e parada após 50 gerações
sem melhoria. Cada configuração é executada com seeds 11, 22 e 33. O perfil
`quick`, destinado apenas à verificação do pipeline, reduz esses limites.

## Cenários iniciais

Os resultados versionados cobrem:

- cenário pequeno, para inspeção e confirmação do comportamento;
- cenário médio, para observar estabilidade e custo computacional.

O cenário crítico será incorporado à rodada final de avaliação e o cenário
inviável é utilizado nos testes de restrições, não na comparação de qualidade.

## Métricas registradas

Cada execução armazena:

- custo total, objetivo e penalidades;
- viabilidade;
- distância e custo operacional;
- custo de atendimento prioritário;
- veículos utilizados;
- tempo de execução;
- seed, gerações e motivo de parada;
- rotas resultantes;
- melhor custo de cada geração.

O JSON preserva os dados completos para gráficos e análises posteriores. O
Markdown agrega custo, desvio populacional, distância e tempo médio por grupo.

## Reprodução

Executar a rodada documentada:

```bash
python scripts/executar_experimentos.py
```

Executar uma verificação mais curta:

```bash
python scripts/executar_experimentos.py --profile quick
```

Selecionar cenários e seeds:

```bash
python scripts/executar_experimentos.py \
  --scenarios pequeno medio critico \
  --seeds 11 22 33
```

As saídas padrão são:

- `reports/experiments/resultados-iniciais.json`;
- `reports/experiments/resultados-iniciais.md`.

Tempos de execução dependem do ambiente. Para comparações formais, todas as
abordagens devem ser executadas na mesma máquina, sem misturar rodadas.
