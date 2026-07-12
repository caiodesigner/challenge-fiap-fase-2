# Fitness e restrições

## Visão geral

A classe `RoutingFitness` transforma um cromossomo multirrota em um custo a ser
minimizado pelo algoritmo genético. Além do valor total, a avaliação retorna os
componentes do objetivo, as métricas de cada veículo e todas as violações
encontradas.

O módulo foi separado em quatro responsabilidades:

- `domain.models`: entidades imutáveis e validação dos dados de entrada;
- `domain.scenario`: conversão dos cenários JSON para o domínio;
- `optimization.distance`: matriz de distâncias Haversine;
- `optimization.constraints`: diagnóstico prévio de inviabilidade;
- `optimization.fitness`: objetivos, métricas e penalidades.

## Distâncias e tempo estimado

As distâncias são calculadas pela fórmula Haversine a partir das coordenadas dos
cenários. A matriz é simétrica, pré-calculada uma vez por problema e inclui o
depósito e todas as entregas.

Cada rota considera:

1. saída do depósito;
2. deslocamentos entre entregas na ordem do cromossomo;
3. retorno ao depósito.

Para estimar o momento de atendimento, a configuração inicial adota velocidade
média de 30 km/h e dez minutos de serviço por parada. Esses valores são
configuráveis e não representam dados de trânsito em tempo real.

## Função objetivo

Para uma solução sem violações, o custo é:

```text
objetivo =
    w_distancia  × distância_total_km / 100
  + w_operacao   × custo_operacional / 1.000
  + w_prioridade × custo_atendimento_prioritário / 1.000
  + w_veiculos   × veículos_utilizados / veículos_do_cenário
```

Os pesos iniciais são:

| Componente | Peso |
|---|---:|
| Distância | 1,00 |
| Custo operacional | 1,00 |
| Atendimento prioritário | 2,00 |
| Veículos utilizados | 0,25 |

O custo operacional de uma rota utilizada é o custo fixo do veículo mais sua
distância multiplicada pelo custo por quilômetro. Rotas vazias não geram custo.

## Prioridade e prazo

Para cada entrega, o custo de atendimento combina:

```text
peso_prioridade × (minutos_até_atendimento + 2 × minutos_de_atraso)
```

Os pesos vêm do cenário: crítica = 4, alta = 3, normal = 2 e baixa = 1. Assim,
uma entrega crítica tende a aparecer antes mesmo quando ainda está dentro do
prazo. Quando existe prazo-alvo, atrasos recebem penalização adicional.

## Restrições duras

O plano final somente é considerado executável quando não apresenta nenhuma
das violações abaixo:

| Código | Condição |
|---|---|
| `missing_delivery` | Entrega do cenário ausente do cromossomo |
| `duplicate_delivery` | Entrega repetida no plano |
| `unknown_delivery` | ID que não pertence ao cenário |
| `vehicle_count_mismatch` | Quantidade de rotas diferente da frota |
| `unavailable_vehicle` | Rota atribuída a veículo indisponível |
| `capacity_exceeded` | Carga da rota acima da capacidade |
| `range_exceeded` | Distância da rota acima da autonomia |

O cromossomo já impede duplicações por construção, mas a fitness mantém essa
regra documentada para proteger futuras representações ou fontes externas.

## Penalidades

As penalidades padrão dominam os componentes normalizados do objetivo:

| Violação | Penalidade padrão |
|---|---:|
| Entrega ausente, duplicada ou desconhecida | 100.000 por ocorrência |
| Quantidade incorreta de veículos | 100.000 por diferença |
| Veículo indisponível | 100.000 por rota usada |
| Capacidade excedida | 10.000 por unidade excedente |
| Autonomia excedida | 10.000 por quilômetro excedente |

Os pesos estão em `FitnessWeights` e poderão ser calibrados nos experimentos.
Uma avaliação é marcada como viável somente quando sua lista de violações está
vazia.

## Diagnóstico antes da otimização

`find_feasibility_issues` detecta condições necessárias de inviabilidade:

- inexistência de veículos disponíveis;
- demanda total maior que a capacidade agregada;
- entrega indivisível maior que todos os veículos;
- destino cujo percurso mínimo de ida e volta excede toda a frota.

Esse diagnóstico não substitui a otimização e não prova que um cenário é
viável. Ele identifica impossibilidades evidentes para evitar uma execução sem
chance de sucesso.

## Integração com o algoritmo genético

```python
from rotas_medicas.domain import load_scenario
from rotas_medicas.genetic import GeneticAlgorithm, GeneticConfig
from rotas_medicas.optimization import RoutingFitness

problem = load_scenario("data/cenario_pequeno.json")
fitness = RoutingFitness(problem)
algorithm = GeneticAlgorithm(GeneticConfig(seed=problem.metadata.seed))

result = algorithm.run(
    problem.delivery_ids,
    len(problem.vehicles),
    fitness,
)
evaluation = fitness.evaluate(result.best_chromosome)
```

`evaluation` contém custos, distância, utilização da frota, métricas por rota e
violações explicadas, permitindo auditoria e futura apresentação na interface.
