# Algoritmo genético

## Responsabilidade desta etapa

O módulo `rotas_medicas.genetic` implementa um motor genético reutilizável para
problemas de minimização. Ele controla a evolução das soluções, mas não conhece
distâncias, capacidades, autonomia ou prioridades. Essas regras serão
incorporadas pela função de custo na etapa de fitness e restrições.

Essa separação permite testar os operadores de forma isolada e comparar
diferentes funções de avaliação sem alterar o algoritmo genético.

## Representação genética

O cromossomo é uma tupla imutável de rotas:

```text
Veículo 1: [ENT-004, ENT-001]
Veículo 2: [ENT-003]
Veículo 3: [ENT-002, ENT-005]
```

Cada posição externa corresponde a um veículo. Uma rota vazia representa um
veículo não utilizado. A concatenação das rotas forma uma permutação de todas as
entregas.

Invariantes garantidas pelo `RouteChromosome`:

- existe ao menos um veículo e uma entrega;
- identificadores não são vazios;
- nenhuma entrega aparece duas vezes;
- a conversão de uma permutação para rotas não perde elementos.

## População inicial

Para cada indivíduo:

1. as entregas são embaralhadas;
2. cada entrega é associada aleatoriamente a um veículo;
3. o resultado é validado pelo cromossomo.

Uma instância de `random.Random` é criada com a seed configurada. Dessa forma,
os experimentos podem ser reproduzidos exatamente.

## Seleção e elitismo

A seleção utiliza torneio: uma amostra de indivíduos é escolhida e o de menor
custo se torna pai. O tamanho do torneio controla a pressão seletiva.

Os melhores indivíduos de cada geração são copiados diretamente para a próxima
população. Esse elitismo garante que o melhor custo conhecido não piore ao longo
da execução.

## Crossover

O crossover de ordem (OX) é apropriado para permutações:

1. um segmento do primeiro pai é preservado;
2. as posições restantes são preenchidas na ordem em que aparecem no outro pai;
3. cada filho herda os tamanhos de rota de um dos pais.

Assim, o conjunto de entregas e a quantidade de veículos são preservados sem
duplicações.

## Mutações

O motor escolhe uniformemente uma destas operações quando a mutação é ativada:

- **troca:** troca a posição de duas entregas;
- **inversão:** inverte um trecho da permutação;
- **realocação:** move uma entrega de um veículo para outro.

Troca e inversão exploram novas ordens de visita. Realocação também explora
outras distribuições de carga entre os veículos.

## Critérios de parada

A execução termina pelo primeiro critério satisfeito:

- custo-alvo atingido, quando configurado;
- número de gerações sem melhoria;
- número máximo de gerações.

O resultado registra o motivo da parada, o melhor cromossomo, seu custo e o
histórico de melhor, média e pior custo por geração.

## Parâmetros

| Parâmetro | Padrão | Finalidade |
|---|---:|---|
| `population_size` | 100 | Quantidade de indivíduos |
| `max_generations` | 500 | Limite de gerações |
| `crossover_rate` | 0,90 | Probabilidade de crossover |
| `mutation_rate` | 0,20 | Probabilidade de mutação por filho |
| `elite_count` | 2 | Melhores indivíduos preservados |
| `tournament_size` | 3 | Participantes por torneio |
| `stagnation_generations` | 100 | Limite sem melhoria |
| `target_cost` | ausente | Custo suficiente para parada antecipada |
| `improvement_tolerance` | 1e-9 | Melhoria mínima considerada relevante |
| `seed` | ausente | Reprodutibilidade da execução |

Os valores definitivos serão avaliados experimentalmente em etapa posterior.

## Exemplo de integração

```python
from rotas_medicas.genetic import GeneticAlgorithm, GeneticConfig

config = GeneticConfig(population_size=80, max_generations=300, seed=42)
algorithm = GeneticAlgorithm(config)

result = algorithm.run(
    delivery_ids=("ENT-001", "ENT-002", "ENT-003"),
    vehicle_count=2,
    cost_function=minha_funcao_de_custo,
)
```

`minha_funcao_de_custo` deve receber um cromossomo e retornar um número finito.
Custos menores são considerados melhores.
