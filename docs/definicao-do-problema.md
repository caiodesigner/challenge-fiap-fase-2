# Definição do problema e critérios de avaliação

## 1. Contexto

O sistema deverá planejar a distribuição de medicamentos e insumos partindo de
um centro de distribuição hospitalar para unidades de saúde e endereços de
atendimento domiciliar. O planejamento deverá determinar quais entregas serão
atendidas por cada veículo e em qual ordem, respeitando limitações operacionais
e dando tratamento adequado às entregas prioritárias.

O problema será tratado como uma variante do **Problema de Roteamento de
Veículos com Capacidade (CVRP)**, com frota heterogênea, autonomia máxima e
prioridades de entrega. O algoritmo genético buscará uma solução de boa
qualidade em tempo viável, sem a exigência de provar que encontrou o ótimo
global.

## 2. Objetivo do sistema

Produzir um plano de rotas executável que:

1. atenda todas as entregas válidas exatamente uma vez;
2. respeite a capacidade e a autonomia de cada veículo;
3. priorize medicamentos e insumos críticos;
4. reduza a distância total percorrida;
5. use a frota de maneira eficiente;
6. forneça dados suficientes para visualização, instruções aos motoristas e
   relatórios gerenciais.

## 3. Escopo

### 3.1 Incluído na primeira versão

- um único depósito central, de onde os veículos saem e para onde retornam;
- múltiplos veículos, que podem ter capacidades e autonomias diferentes;
- entregas para unidades hospitalares e atendimento domiciliar;
- demanda de carga e nível de prioridade por entrega;
- coordenadas geográficas dos pontos;
- cálculo de custo com base em uma matriz de distâncias;
- penalização de soluções que violem restrições;
- comparação da solução genética com abordagens de referência;
- indicadores operacionais e dados para plotagem das rotas em mapa.

### 3.2 Fora do escopo inicial

- atualização das rotas em tempo real;
- trânsito em tempo real e bloqueios de vias;
- coletas, devoluções e logística reversa;
- entregas fracionadas entre veículos;
- múltiplos depósitos;
- escalas e jornadas de motoristas;
- controle de temperatura ou compatibilidade entre cargas;
- comprovação matemática da solução ótima.

Esses itens poderão ser tratados como evoluções, sem alterar o objetivo central
do desafio.

## 4. Premissas de modelagem

- Cada execução representa um período de planejamento, como um dia de
  entregas.
- Todos os veículos começam e terminam no mesmo depósito.
- Cada veículo realiza no máximo uma rota por execução.
- Uma entrega é indivisível e deve pertencer a uma única rota.
- A demanda e a capacidade usam a mesma unidade de carga. A unidade concreta
  poderá ser quilogramas, volumes ou uma unidade logística padronizada.
- As distâncias são não negativas e conhecidas antes da otimização.
- O tempo de serviço e a velocidade média não fazem parte da restrição inicial;
  quando necessários para relatórios, serão estimados separadamente.
- Entregas críticas serão representadas por prioridade e prazo-alvo. A
  prioridade não autoriza violar capacidade ou autonomia.
- Instâncias impossíveis deverão ser rejeitadas ou sinalizadas, em vez de serem
  apresentadas como planos executáveis.

## 5. Entidades do domínio

### 5.1 Depósito

| Campo | Descrição | Regra |
|---|---|---|
| `id` | Identificador único | Obrigatório |
| `nome` | Nome do centro de distribuição | Obrigatório |
| `latitude` | Latitude em graus decimais | Entre -90 e 90 |
| `longitude` | Longitude em graus decimais | Entre -180 e 180 |

### 5.2 Entrega

| Campo | Descrição | Regra |
|---|---|---|
| `id` | Identificador único | Obrigatório e não repetido |
| `destino` | Nome da unidade ou identificação não sensível do destino | Obrigatório |
| `tipo_destino` | Unidade de saúde ou atendimento domiciliar | Valor enumerado |
| `latitude` | Latitude do destino | Entre -90 e 90 |
| `longitude` | Longitude do destino | Entre -180 e 180 |
| `demanda` | Quantidade de carga necessária | Maior que zero |
| `prioridade` | Criticidade da entrega | Crítica, alta, normal ou baixa |
| `prazo_alvo` | Limite desejado desde a saída do depósito | Positivo, quando informado |
| `descricao_carga` | Descrição operacional dos itens | Sem dados clínicos pessoais |

Os níveis de prioridade terão pesos configuráveis. Como valores iniciais para
os experimentos, serão usados: crítica = 4, alta = 3, normal = 2 e baixa = 1.

### 5.3 Veículo

| Campo | Descrição | Regra |
|---|---|---|
| `id` | Identificador único | Obrigatório e não repetido |
| `descricao` | Nome ou identificação operacional | Obrigatório |
| `capacidade` | Carga máxima transportável | Maior que zero |
| `autonomia_km` | Distância máxima da rota | Maior que zero |
| `custo_fixo` | Custo de utilizar o veículo | Maior ou igual a zero |
| `custo_por_km` | Custo variável de deslocamento | Maior ou igual a zero |
| `disponivel` | Indica participação na execução | Booleano |

### 5.4 Rota e plano de rotas

Uma rota associa um veículo a uma sequência ordenada de entregas. A distância
da rota inclui a saída do depósito, todos os deslocamentos entre entregas e o
retorno ao depósito.

O plano de rotas é o conjunto das rotas da frota e deverá registrar, no mínimo:

- sequência de paradas por veículo;
- distância e carga de cada rota;
- distância total do plano;
- entregas atendidas e não atendidas;
- violações encontradas;
- valor e componentes da função de avaliação.

## 6. Restrições

### 6.1 Restrições obrigatórias (duras)

Uma solução somente será considerada executável quando:

- cada entrega aparecer exatamente uma vez no plano;
- somente veículos disponíveis forem utilizados;
- a soma das demandas de uma rota não exceder a capacidade do veículo;
- a distância total de uma rota não exceder a autonomia do veículo;
- toda rota começar e terminar no depósito;
- todos os identificadores e valores de entrada forem válidos.

Durante a evolução, o algoritmo poderá gerar indivíduos inválidos. Eles deverão
ser reparados ou receber penalidades suficientemente altas para não serem
preferidos a soluções executáveis.

### 6.2 Critérios de otimização (restrições suaves)

- atender entregas de maior prioridade mais cedo;
- evitar ultrapassar o prazo-alvo de uma entrega;
- reduzir a distância total;
- reduzir o custo operacional;
- evitar veículos ociosos quando isso aumentar desnecessariamente a distância,
  sem obrigar o uso de toda a frota;
- distribuir a carga de modo operacionalmente razoável quando duas soluções
  apresentarem custo semelhante.

## 7. Função objetivo

O algoritmo minimizará uma função de custo composta:

```text
custo =
    w_distancia * distancia_total_normalizada
  + w_operacao  * custo_operacional_normalizado
  + w_atraso    * atraso_ponderado_por_prioridade
  + w_veiculos  * veiculos_utilizados_normalizado
  + penalidades_por_violacoes
```

Em que o atraso ponderado de uma entrega é proporcional ao atraso em relação ao
seu prazo-alvo e ao peso de sua prioridade. Entregas sem prazo-alvo ainda serão
favorecidas pela sua posição na rota de acordo com a prioridade.

Os pesos não serão fixados como regra de negócio nesta etapa. Eles serão
configuráveis e calibrados experimentalmente, com os seguintes princípios:

1. violações de restrições duras devem dominar qualquer ganho de distância;
2. atrasos de entregas críticas devem custar mais que atrasos de baixa
   prioridade;
3. entre soluções executáveis com nível de serviço equivalente, vence a de
   menor custo operacional e distância.

Caso a implementação use uma fitness que deva ser maximizada, ela será derivada
do custo, por exemplo `fitness = 1 / (1 + custo)`, preservando a mesma ordenação
das soluções.

## 8. Métricas de avaliação

### 8.1 Qualidade da solução

| Métrica | Definição | Direção desejada |
|---|---|---|
| Taxa de atendimento | Entregas atendidas / entregas válidas | 100% |
| Violações duras | Quantidade de violações no plano final | 0 |
| Distância total | Soma das distâncias de todas as rotas | Menor |
| Custo operacional | Custos fixos e variáveis da frota usada | Menor |
| Atraso ponderado | Atraso multiplicado pelo peso da prioridade | Menor |
| Pontualidade crítica | Críticas dentro do prazo / críticas | Maior |
| Veículos utilizados | Rotas não vazias | Menor, sem degradar o serviço |
| Utilização de carga | Carga transportada / capacidade usada | Análise |
| Utilização de autonomia | Distância da rota / autonomia | Abaixo de 100% |

### 8.2 Desempenho do otimizador

- tempo total de execução;
- melhor custo encontrado por geração;
- geração da última melhoria;
- variabilidade entre execuções com sementes diferentes;
- diferença percentual em relação às abordagens de referência.

## 9. Abordagens de referência

Para que a melhoria seja mensurável, o algoritmo genético será comparado, no
mínimo, com:

- uma solução gulosa baseada no vizinho mais próximo, adaptada às restrições;
- uma heurística que ordene primeiro por prioridade e depois por distância.

Em instâncias pequenas, poderá ser incluída uma solução exata ou uma biblioteca
de otimização reconhecida como referência adicional. Todas as abordagens deverão
receber os mesmos dados e ser avaliadas pelas mesmas métricas.

## 10. Cenários mínimos de validação

| Cenário | Finalidade | Características mínimas |
|---|---|---|
| Pequeno | Validar regras e inspecionar a rota manualmente | 1 depósito, 1–2 veículos e 5–10 entregas |
| Médio | Comparar qualidade e estabilidade | Múltiplos veículos e 20–50 entregas variadas |
| Crítico | Avaliar prioridades e limites operacionais | Alta demanda, prioridades distintas e pouca folga de capacidade/autonomia |
| Inviável | Validar detecção de impossibilidade | Ao menos uma entrega ou conjunto impossível de atender |

## 11. Critérios de aceite desta definição

A implementação futura estará aderente a esta especificação quando:

1. aceitar depósito, entregas e frota com os campos definidos neste documento;
2. produzir rotas com início e fim no depósito;
3. atender cada entrega exatamente uma vez em cenários viáveis;
4. não exceder capacidade nem autonomia no plano final;
5. considerar explicitamente múltiplos veículos e prioridades na avaliação;
6. identificar cenários inviáveis com uma justificativa verificável;
7. calcular e expor as métricas de qualidade definidas;
8. ser executável de forma determinística quando receber a mesma semente;
9. superar ou justificar o resultado diante das abordagens de referência;
10. disponibilizar a sequência e as coordenadas necessárias para o mapa e os
    dados estruturados necessários para a futura integração com LLM.

## 12. Decisões adiadas

As seguintes decisões pertencem às próximas etapas e não são definidas aqui:

- formato físico dos arquivos de entrada e saída;
- biblioteca de mapas ou de cálculo de distâncias;
- codificação genética e operadores de evolução;
- valores finais dos pesos e penalidades;
- tecnologia da API e da interface;
- provedor e modelo de LLM;
- estratégia de implantação em nuvem.
