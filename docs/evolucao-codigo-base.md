# Evolução do código-base de TSP

## Referência e versão analisada

O ponto de partida indicado para o challenge é o repositório
[`sergiopolimante/genetic_algorithm_tsp`](https://github.com/sergiopolimante/genetic_algorithm_tsp),
analisado no commit
[`1be73eccfd110a3314cc28dae5a8e78a4dcca9bb`](https://github.com/sergiopolimante/genetic_algorithm_tsp/commit/1be73eccfd110a3314cc28dae5a8e78a4dcca9bb).

O arquivo `LICENSE` do repositório contém a dedicação CC0 1.0 Universal. O
README menciona MIT, mas diverge do arquivo de licença; por isso, esta entrega
registra a licença encontrada no arquivo próprio. Não há cópia dos arquivos
originais no produto final: seus conceitos foram refatorados e estendidos na
arquitetura do projeto.

## Funcionamento original

O código-base resolve um TSP simétrico e didático:

1. cada cidade é uma coordenada `(x, y)` e cada indivíduo é uma permutação;
2. a população nasce de amostras aleatórias das cidades;
3. a fitness soma distâncias euclidianas e fecha o circuito;
4. a seleção escolhe indivíduos melhores;
5. o Order Crossover preserva um trecho e completa a ordem pelo outro pai;
6. a mutação troca cidades adjacentes;
7. o melhor indivíduo sobrevive por elitismo;
8. o Pygame desenha cidades, circuito e convergência.

Esse modelo possui uma rota, nenhuma entidade de depósito ou veículo e nenhum
atributo operacional além da posição.

## Rastreabilidade da evolução

| Elemento | Código-base | Solução médica |
|---|---|---|
| Gene | coordenada da cidade | ID único da entrega |
| Cromossomo | permutação única | permutação particionada em rotas por veículo |
| Circuito | cidades e retorno à primeira | depósito, entregas e retorno ao depósito |
| População | permutações aleatórias | permutações e atribuições aleatórias à frota |
| Distância | euclidiana em pixels | Haversine em quilômetros |
| Fitness | distância total | distância, custo, prioridade, frota e penalidades |
| Seleção | melhores ou peso inverso | torneio configurável |
| Crossover | OX com um filho | OX com dois filhos e partições multirrota |
| Mutação | troca adjacente | troca, inversão e realocação entre veículos |
| Elitismo | um indivíduo | quantidade configurável |
| Parada | laço da visualização | gerações, estagnação ou custo-alvo |
| Visualização | Pygame cartesiano | Leaflet geográfico, GeoJSON e SVG |

O núcleo conceitual preservado é:

```text
permutação -> população -> avaliação -> seleção -> OX -> mutação -> elitismo
```

A extensão para o contexto hospitalar é:

```text
TSP de uma rota
    -> IDs e depósito explícito
    -> partição por veículo
    -> VRP com carga e autonomia
    -> prioridade e custo operacional
    -> validação, API, mapa e relatórios
```

## Modificações necessárias

### Representação multirrota

`RouteChromosome` mantém uma rota por posição de veículo. A concatenação ainda é
uma permutação, como no código-base, mas a partição permite mudar a atribuição de
entregas entre veículos. Uma rota vazia representa veículo não utilizado.

### Operadores especializados

O OX permanece apropriado para preservar todas as entregas exatamente uma vez.
Cada filho herda uma partição de rotas. A realocação foi adicionada porque troca
e inversão alteram somente a ordem; sem ela, o algoritmo não exploraria novas
distribuições de carga na frota.

### Fitness e restrições

A distância deixou de ser o único objetivo. A avaliação passou a decompor
distância, custo operacional, atendimento prioritário e uso de veículos. Carga,
autonomia, disponibilidade e cobertura recebem penalidades dominantes e geram
violações explicáveis.

### Coordenadas e visualização

Como os cenários usam latitude e longitude, a distância euclidiana em pixels foi
substituída por Haversine. A visualização Pygame foi substituída por mapa Leaflet
e artefatos portáveis. As linhas representam aproximações geodésicas, não vias.

### Engenharia e reprodutibilidade

O estado aleatório global foi substituído por `random.Random` com seed. A
configuração passou a validar taxas e tamanhos; o motor registra histórico e
motivo da parada. Domínio, algoritmo, fitness, interface e visualização foram
separados e cobertos por testes automatizados.

## Limitações corrigidas do original

O repositório-base é adequado como demonstração, mas não como aplicação
hospitalar. A refatoração também evita estas limitações observadas:

- `tsp.py` chama o crossover com `parent1` nos dois argumentos, apesar de
  selecionar dois pais;
- a execução visual não aplica um limite efetivo de gerações;
- não existem testes automatizados nem validação das permutações;
- não há separação entre entidades, evolução, fitness e interface;
- coordenadas são os próprios genes, dificultando atributos adicionais;
- imports duplicados e referências incompletas aparecem nos auxiliares gráficos.

Corrigir esses pontos foi necessário para produzir uma solução determinística,
testável e extensível, sem manter uma segunda implementação Pygame sem uso.

## Decisão sobre incorporação

Os arquivos originais não foram copiados para `src/`. Mantê-los criaria duas
implementações concorrentes e adicionaria Pygame, NumPy e Matplotlib sem função
no runtime. A rastreabilidade é preservada por esta comparação, pelos conceitos
mantidos nos módulos `genetic` e pelos testes dos operadores e invariantes.
