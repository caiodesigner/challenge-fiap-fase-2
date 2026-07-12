# Arquitetura da solução

## Visão de contexto

O sistema apoia uma equipe logística hospitalar no planejamento de entregas. O
operador seleciona um cenário, configura a otimização, analisa rotas e métricas
e pode solicitar conteúdo em linguagem natural. Serviços externos não participam
do cálculo da solução.

```mermaid
flowchart LR
    O[Operador logístico] -->|HTTP| W[Interface web]
    W --> A[API FastAPI]
    A --> G[Motor genético]
    A --> V[Visualização]
    A --> L[Assistente de linguagem]
    G --> D[(Cenários JSON)]
    L -->|opcional| X[OpenAI Responses API]
    A --> M[(Soluções em memória)]
```

## Componentes

```mermaid
flowchart TB
    subgraph Entrada
        UI[HTML + JavaScript + Leaflet]
        API[API / OpenAPI]
    end

    subgraph Aplicação
        APP[RouteApplicationService]
        STORE[InMemorySolutionStore]
    end

    subgraph Domínio
        MODELS[Depot / Delivery / Vehicle]
        PROBLEM[RoutingProblem]
    end

    subgraph Otimização
        GA[GeneticAlgorithm]
        FIT[RoutingFitness]
        BASE[Baselines]
        DIST[DistanceMatrix]
        EXP[Experimentos]
    end

    subgraph Linguagem
        PROMPT[Prompts versionados]
        LLM[RouteLanguageService]
        PROVIDER[LLMProvider]
        QUALITY[QualityAssessment]
    end

    subgraph Saída
        GEO[GeoJSON / mapas]
        REPORTS[JSON / Markdown / SVG]
    end

    UI --> API --> APP
    APP --> PROBLEM
    APP --> GA
    APP --> FIT
    APP --> STORE
    GA --> FIT
    FIT --> DIST
    BASE --> FIT
    EXP --> GA
    EXP --> BASE
    APP --> LLM
    LLM --> PROMPT
    LLM --> PROVIDER
    LLM --> QUALITY
    APP --> GEO
    EXP --> REPORTS
    MODELS --> PROBLEM
```

## Fluxo de uma otimização

```mermaid
sequenceDiagram
    actor Operador
    participant UI as Interface
    participant API as FastAPI
    participant App as Aplicação
    participant GA as Algoritmo genético
    participant Fit as Fitness
    participant Store as Memória

    Operador->>UI: Seleciona cenário e parâmetros
    UI->>API: POST /api/optimize
    API->>App: optimize(...)
    App->>App: Carrega e valida cenário
    App->>App: Detecta inviabilidades evidentes
    App->>GA: run(entregas, veículos, fitness)
    loop Gerações
        GA->>Fit: Avalia população
        Fit-->>GA: Objetivos + penalidades
    end
    GA-->>App: Melhor cromossomo + histórico
    App->>Fit: Confirma plano final
    App->>Store: Salva por UUID
    App-->>API: SolutionRecord
    API-->>UI: Métricas + rotas + GeoJSON
    UI-->>Operador: Mapa e indicadores
```

## Fluxo da LLM

```mermaid
sequenceDiagram
    actor Operador
    participant API
    participant App as Aplicação
    participant Lang as RouteLanguageService
    participant Provider as LLMProvider
    participant Validator as Validação determinística

    Operador->>API: Solicita instrução, relatório ou resposta
    API->>App: Caso de uso com solution_id
    App->>Lang: Problema + cromossomo + fitness
    Lang->>Lang: Monta contexto JSON mínimo
    Lang->>Provider: Prompt + contrato Pydantic
    Provider-->>Lang: Resposta estruturada
    Lang->>Validator: Confere IDs e sequência
    alt Resposta fundamentada
        Validator-->>API: Conteúdo + qualidade
        API-->>Operador: Resposta
    else Divergência
        Validator-->>API: LLMValidationError
        API-->>Operador: Falha controlada
    end
```

## Dependências entre camadas

As dependências apontam da borda para o núcleo:

```text
api -> application -> domain
                  -> genetic -> domain
                  -> optimization -> domain + genetic
                  -> llm -> domain + optimization
                  -> visualization -> domain + optimization
```

O domínio não importa FastAPI, OpenAI ou bibliotecas de visualização. O motor
genético também não conhece o contexto hospitalar: ele recebe uma função de
custo injetável.

## Decisões arquiteturais

### Cromossomo multirrota imutável

Uma tupla externa representa veículos e cada tupla interna representa a ordem
das entregas. A imutabilidade torna indivíduos seguros para elitismo, comparação
e testes. Entregas duplicadas são rejeitadas na criação.

### Fitness explicável

O custo total é decomposto em objetivo e penalidades. A API pode mostrar
distância, custo, prioridade, carga, autonomia e violações sem recalcular dados.

### Haversine em vez de roteador viário

A primeira versão usa coordenadas e distância de grande círculo, o que mantém a
demonstração determinística e sem serviço externo. As linhas no mapa são
aproximações, não trajetos por ruas.

### LLM fora do caminho crítico

Uma indisponibilidade da LLM não impede calcular rotas. O modelo recebe apenas o
plano final e não participa da função fitness. O provedor local permite testes e
demonstração sem rede.

### Estado em memória

Soluções da API são mantidas em um store protegido por lock. Essa escolha reduz
a infraestrutura da demonstração, mas não oferece persistência após reinício nem
coordenação entre réplicas.

## Escalabilidade e evolução

Para produção, a arquitetura pode evoluir sem alterar o domínio:

- PostgreSQL ou armazenamento de objetos para soluções e relatórios;
- fila de tarefas para otimizações longas;
- serviço de matriz viária com trânsito e janelas de tempo;
- autenticação, autorização e trilha de auditoria;
- cache por cenário e configuração;
- métricas Prometheus e tracing;
- múltiplos depósitos e entregas fracionadas;
- implantação containerizada com múltiplas réplicas.

Implementação em nuvem e infraestrutura como código não fazem parte da versão
atual, conforme a natureza opcional desse item no enunciado.
