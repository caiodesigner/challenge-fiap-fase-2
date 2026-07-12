# Relatório técnico — Otimização de Rotas Médicas

## 1. Resumo executivo

Este projeto resolve uma variante hospitalar do Problema de Roteamento de
Veículos com Capacidade (CVRP). O sistema distribui medicamentos e insumos a
unidades de saúde e atendimentos domiciliares, considerando múltiplos veículos,
capacidade, autonomia e prioridades.

A solução combina:

- algoritmo genético especializado em permutações e múltiplas rotas;
- função fitness explicável com objetivos e penalidades;
- três heurísticas de referência;
- experimentos reproduzíveis com três configurações e três seeds;
- mapas, indicadores, GeoJSON e convergência;
- integração segura com LLM para instruções, relatórios e perguntas;
- API FastAPI e interface web;
- 110 testes automatizados e 94,22% de cobertura.

Nos experimentos iniciais, a melhor configuração genética média reduziu o custo
composto em 25,85% no cenário pequeno e 27,75% no médio em relação ao melhor
baseline de cada cenário. Todas as 24 execuções produziram planos viáveis.

## 2. Problema e escopo

Cada execução contém um depósito, entregas indivisíveis e uma frota heterogênea.
O sistema deve atribuir cada entrega exatamente uma vez e ordenar as paradas de
cada veículo.

Restrições obrigatórias:

- prioridades crítica, alta, normal e baixa;
- capacidade máxima por veículo;
- autonomia máxima por rota;
- múltiplos veículos;
- saída e retorno ao mesmo depósito;
- cobertura completa das entregas.

O escopo atual usa um depósito, uma rota por veículo e distâncias Haversine. Não
inclui trânsito em tempo real, múltiplos depósitos, entregas fracionadas, coletas
ou janelas rígidas de tempo.

A especificação detalhada está em [Definição do problema](definicao-do-problema.md).

## 3. Dados

Foram criados quatro cenários sintéticos e determinísticos:

| Cenário | Entregas | Veículos | Objetivo |
|---|---:|---:|---|
| Pequeno | 8 | 2 | Inspeção manual |
| Médio | 30 | 5 | Comparação e estabilidade |
| Crítico | 18 | 3 | Prioridades e pouca folga |
| Inviável | 6 | 2 | Diagnóstico de impossibilidade |

O cenário inviável contém uma entrega indivisível maior que qualquer veículo. Os
arquivos seguem um JSON Schema versionado e não contêm dados pessoais ou
clínicos reais. Consulte [Dados de demonstração](../data/README.md).

## 4. Implementação do algoritmo genético

### 4.1 Representação

O cromossomo é uma tupla imutável de rotas. A posição externa representa o
veículo e cada sequência interna contém IDs de entrega na ordem de visita.

```text
(
  (ENT-004, ENT-001),
  (ENT-003,),
  (ENT-002, ENT-005)
)
```

Uma rota vazia significa veículo não utilizado. O cromossomo rejeita IDs vazios
e duplicados e preserva o conjunto completo durante crossover e mutações.

### 4.2 População

Cada indivíduo começa com uma permutação aleatória das entregas, distribuída
entre as posições da frota. A seed configurável torna toda execução
reproduzível.

### 4.3 Seleção e elitismo

A seleção usa torneio, escolhendo o menor custo entre indivíduos amostrados. Os
melhores indivíduos são copiados para a geração seguinte. Por isso, o melhor
custo por geração nunca piora.

### 4.4 Crossover

O crossover de ordem (OX) preserva um segmento de um pai e completa as posições
na ordem do outro. Cada descendente herda a divisão de rotas de um dos pais. O
operador mantém uma permutação válida sem duplicar entregas.

### 4.5 Mutações

- troca de duas entregas;
- inversão de um trecho;
- realocação de uma entrega entre veículos.

Troca e inversão exploram ordens. Realocação explora a distribuição da demanda
entre os veículos.

### 4.6 Parada

A execução termina por custo-alvo, estagnação ou máximo de gerações. O resultado
registra motivo, melhor solução e histórico de melhor, média e pior fitness.

O código-base indicado é o repositório
[`sergiopolimante/genetic_algorithm_tsp`](https://github.com/sergiopolimante/genetic_algorithm_tsp),
analisado no commit `1be73eccfd110a3314cc28dae5a8e78a4dcca9bb`. A solução
preserva população aleatória, permutação, OX, mutação, elitismo e minimização da
fitness, mas reestrutura esses conceitos para um VRP médico testável. A
transformação inclui IDs de entrega, depósito explícito, múltiplas rotas,
Haversine, torneio, novas mutações e restrições operacionais. Consulte
[Evolução do código-base](evolucao-codigo-base.md) e
[Algoritmo genético](algoritmo-genetico.md).

## 5. Fitness e restrições

O algoritmo minimiza:

```text
objetivo =
    distância normalizada
  + custo operacional normalizado
  + 2 × atendimento prioritário normalizado
  + 0,25 × utilização da frota
```

O atendimento prioritário considera o tempo estimado até cada parada,
multiplicado pelo peso da prioridade. Atrasos em relação ao prazo-alvo recebem
penalidade adicional.

Violações duras recebem custos dominantes:

| Violação | Penalidade padrão |
|---|---:|
| Entrega ausente, desconhecida ou duplicada | 100.000 |
| Veículo indisponível | 100.000 |
| Quantidade de rotas incompatível | 100.000 |
| Capacidade excedida | 10.000 por unidade |
| Autonomia excedida | 10.000 por km |

A avaliação retorna componentes, métricas por rota e violações, permitindo
auditar por que uma solução venceu. Antes da evolução, condições necessárias de
inviabilidade são verificadas. Detalhes: [Fitness e restrições](fitness-e-restricoes.md).

## 6. Baselines

Três abordagens recebem os mesmos dados e a mesma fitness:

1. ordem original com primeiro veículo viável;
2. vizinho mais próximo global entre pontas de rota;
3. prioridade e distância com inserção viável mais curta.

Quando não existe inserção viável, o baseline preserva a entrega e escolhe a
menor violação estimada. A fitness explicita e penaliza o problema, em vez de
omitir demanda.

## 7. Experimentos

### 7.1 Configurações

| Configuração | População | Gerações | Crossover | Mutação | Elitismo | Torneio |
|---|---:|---:|---:|---:|---:|---:|
| Exploração | 80 | 160 | 0,95 | 0,40 | 2 | 3 |
| Balanceada | 80 | 160 | 0,90 | 0,25 | 3 | 4 |
| Explotação | 80 | 160 | 0,80 | 0,10 | 4 | 6 |

Cada configuração foi executada com seeds 11, 22 e 33 nos cenários pequeno e
médio. Com os três baselines, a rodada totalizou 24 execuções.

### 7.2 Resultados

| Cenário | Abordagem/configuração | Custo médio | Desvio | Distância média |
|---|---|---:|---:|---:|
| Pequeno | GA balanceada | 1,274225 | 0,000000 | 17,009 km |
| Pequeno | Melhor baseline: vizinho | 1,718520 | — | 17,282 km |
| Médio | GA exploração | 7,446300 | 0,068911 | 107,579 km |
| Médio | Melhor baseline: vizinho | 10,306886 | — | 96,460 km |

No médio, o baseline percorreu menos distância que a média genética, mas obteve
custo composto pior. Isso ocorre porque a fitness também considera prioridade,
custo operacional e uso da frota. Comparar apenas quilômetros ocultaria o nível
de serviço definido pelo projeto.

A melhor execução individual do médio foi a configuração balanceada com seed
11: fitness 7,345609 e distância 93,933 km.

Resultados completos:

- [Resumo Markdown](../reports/experiments/resultados-iniciais.md)
- [Dados JSON](../reports/experiments/resultados-iniciais.json)
- [Metodologia experimental](baselines-e-experimentos.md)

## 8. Visualizações

Para pequeno e médio foram gerados:

- mapa HTML interativo;
- painel HTML de indicadores;
- GeoJSON de rotas e paradas;
- SVG de convergência.

Cada veículo tem uma cor e cada prioridade possui marcador distinto. Popups
mostram ordem, veículo, demanda e destino sintético. Os painéis exibem carga e
autonomia absoluta e percentual.

Exemplos:

- [Mapa do cenário pequeno](../reports/visualizations/pequeno.mapa.html)
- [Mapa do cenário médio](../reports/visualizations/medio.mapa.html)
- [Convergência do cenário médio](../reports/visualizations/medio.convergencia.svg)

As linhas ligam coordenadas diretamente, pois ainda não há roteador viário.
Consulte [Visualizações](visualizacoes.md).

## 9. Integração com LLM

### 9.1 Casos de uso

- instruções detalhadas por veículo e parada;
- relatório diário ou semanal;
- perguntas em linguagem natural sobre rotas e entregas.

### 9.2 Abordagem

`RouteLanguageService` monta um contexto JSON com fatos calculados e solicita
Structured Outputs validados por Pydantic. `LLMProvider` desacopla a aplicação do
fornecedor. Existe um adaptador para OpenAI Responses API, um provedor de fila
para testes e um fallback local explicitamente identificado como não LLM.

A LLM não calcula rotas. Instruções que trocam sequência ou veículos são
rejeitadas. Respostas com IDs inexistentes também falham. O prompt proíbe dados
inventados e orientação clínica.

### 9.3 Prompts

Os prompts versionados incluem:

- regras permanentes no prompt de sistema;
- dados delimitados em `<dados_json>`;
- tarefa específica para instrução, relatório ou pergunta;
- obrigação de declarar insuficiência de dados;
- comparação calculada contra o melhor baseline viável;
- obrigação de fundamentar melhorias em métricas, cargas, prioridades e rotas.

### 9.4 Avaliação

A avaliação determinística mede cobertura, sequência e validade das evidências.
Os exemplos locais alcançaram 1,0 nessas métricas nos dois cenários. O relatório
inclui economia de distância, custo e tempo estimado calculada pelo sistema, sem
delegar aritmética à LLM. A avaliação humana possui script próprio com notas de
clareza, utilidade, segurança e fundamentação.

Os artefatos em `reports/llm` foram gerados pelo modo local, não pela OpenAI. Uma
chamada real exige `OPENAI_API_KEY` e deve ser executada pelo grupo antes da
gravação do vídeo caso a demonstração externa seja desejada. Consulte
[Integração com LLM](integracao-llm.md) e
[Validação final antes do vídeo](demonstracao-final.md).

## 10. Interface e API

A interface FastAPI permite selecionar cenário, configurar evolução, otimizar,
analisar o mapa e chamar os três casos de uso de linguagem. A API gera Swagger e
OpenAPI automaticamente.

Soluções recebem UUID e ficam em memória até o servidor reiniciar. Parâmetros
custosos possuem limites HTTP. Cenários inviáveis retornam 422 com diagnóstico.

- [Interface](interface-da-solucao.md)
- [API](api.md)
- [Arquitetura](arquitetura.md)

## 11. Testes e qualidade

O pipeline local e o GitHub Actions executam:

- Ruff lint e formatação;
- mypy estrito;
- Pytest com branches;
- cobertura mínima de 90%;
- `pip check`.

Estado documentado desta entrega: 110 testes aprovados e 94,22% de cobertura. Os
testes da API usam transporte ASGI; testes de LLM não acessam rede. Consulte
[Testes e qualidade](testes-e-qualidade.md).

## 12. Desafios e soluções

### Preservar permutações válidas

Operadores genéticos tradicionais podem duplicar cidades. OX e cromossomo
imutável preservam o conjunto de entregas e falham cedo para duplicações.

### Equilibrar restrições e objetivos

Uma distância curta pode ser impossível. Penalidades dominantes separam
viabilidade de qualidade, enquanto o detalhamento mostra cada excesso.

### Comparar abordagens diferentes

Todas as soluções são avaliadas pela mesma fitness, inclusive baselines. Seeds,
configurações e histórico ficam registrados no JSON experimental.

### Evitar alucinação operacional

A LLM recebe dados estruturados somente após a otimização. Structured Outputs e
validação semântica bloqueiam mudanças de rota e evidências inexistentes.

### Manter demonstração reproduzível

Dados, experimentos, visualizações e conteúdo local possuem scripts próprios.
Nenhum teste depende de API externa ou segredo.

## 13. Limitações

- distância geodésica em vez de malha viária;
- sem trânsito, tempo real ou janelas rígidas;
- dados apenas sintéticos;
- estado da API somente em memória;
- otimização dentro da requisição HTTP;
- sem autenticação e autorização;
- configuração de nuvem validada localmente, mas ainda sem provisionamento em
  projeto externo;
- sem avaliação humana registrada da LLM;
- sem execução real da OpenAI versionada;
- cenário crítico ainda não incluído na matriz experimental completa.

## 14. Próximos passos

1. executar avaliação humana cega das instruções da LLM;
2. adicionar tempo real ou matriz viária;
3. incluir cenário crítico na rodada final;
4. persistir soluções e mover execução para fila;
5. adicionar autenticação e auditoria;
6. provisionar a configuração Cloud Run e registrar evidências da implantação;
7. gravar o vídeo seguindo o roteiro versionado.

## 15. Conclusão

O projeto atende o núcleo técnico do desafio: algoritmo genético multirrota,
prioridade, capacidade, autonomia, múltiplos veículos, comparação com outras
abordagens, visualização e integração de linguagem natural. A separação entre
otimizador e LLM preserva rastreabilidade: decisões logísticas continuam
determinísticas e auditáveis, enquanto a linguagem melhora sua apresentação.
