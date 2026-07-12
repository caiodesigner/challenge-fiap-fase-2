# Integração com LLM

## Objetivo e limites

A LLM transforma rotas e métricas já calculadas em:

- instruções detalhadas para motoristas;
- relatórios diários ou semanais;
- respostas em linguagem natural sobre o plano.

A LLM não calcula, altera ou valida a viabilidade das rotas. O algoritmo
genético e a função fitness continuam sendo a fonte de verdade. Uma resposta
que modificar veículos, entregas ou sequência é rejeitada pelo sistema.

## Arquitetura

`RouteLanguageService` recebe quatro dependências:

1. problema de roteamento;
2. cromossomo final;
3. avaliação detalhada da fitness;
4. provedor de linguagem.

O serviço constrói um contexto JSON mínimo, solicita uma resposta estruturada e
compara o resultado com os dados originais antes de devolvê-lo.

O protocolo `LLMProvider` mantém a aplicação desacoplada do fornecedor. Estão
disponíveis:

- `OpenAIResponsesProvider`: integração real com a OpenAI;
- `QueueProvider`: respostas controladas para testes;
- `RuleBasedProvider`: demonstração local, explicitamente sem LLM externa.

## OpenAI Responses API

O adaptador usa o SDK Python oficial, a Responses API e Structured Outputs:

```python
response = client.responses.parse(
    model=model,
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    text_format=response_model,
)
```

O modelo padrão é `gpt-5.6`, podendo ser substituído por `OPENAI_MODEL`. Os
contratos de resposta são modelos Pydantic com campos extras proibidos.

Referências oficiais:

- [Text generation](https://developers.openai.com/api/docs/guides/text)
- [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## Prompt engineering

O prompt de sistema estabelece regras estáveis:

- usar somente o contexto fornecido;
- não inventar IDs, métricas ou horários;
- não recalcular nem alterar a rota;
- não fornecer orientação clínica;
- declarar dados insuficientes;
- responder em português do Brasil.

Os dados são delimitados por `<dados_json>` e explicitamente tratados como
dados, não como instruções. A pergunta do usuário também fica dentro desse
contexto, reduzindo o risco de uma pergunta alterar as regras do sistema.

Cada tarefa possui um prompt próprio e versionado. A versão atual é `1.1`.

## Respostas estruturadas

### Instruções

`DriverInstructions` contém orientações gerais e rotas por veículo. Cada parada
informa ordem, entrega, destino, prioridade e instrução operacional.

### Relatório

O sistema avalia os três baselines e seleciona o plano viável de menor fitness.
Em seguida, calcula distância, custo, tempo estimado e veículos para a solução
genética e a referência. Economias absolutas e percentuais são anexadas ao
`EfficiencyReport` como `EfficiencyComparison`.

A LLM recebe esses dados para produzir `EfficiencyNarrative`, com resumo,
destaques, riscos, interpretação e sugestões fundamentadas em métricas, cargas,
prioridades e rotas. Ela não calcula nem pode substituir os números da
comparação. Valores negativos são apresentados como piora.

### Perguntas

`RouteAnswer` contém resposta, ressalva e IDs usados como evidência. IDs que não
existem no cenário causam rejeição.

## Validação e qualidade

As instruções são comparadas com o cromossomo final:

- veículos devem coincidir;
- todas as rotas utilizadas devem aparecer;
- entregas devem manter a sequência exata;
- numeração das paradas deve ser contínua.

A avaliação retorna pontuação, validade e lista de problemas. Respostas a
perguntas são avaliadas pela validade dos IDs de evidência. A validação é
determinística e ocorre depois da validação estrutural do Pydantic.

Essas métricas medem fundamentação estrutural, não qualidade linguística ou
utilidade percebida. `scripts/avaliar_conteudo_llm.py` registra avaliação humana
de clareza, utilidade, segurança e fundamentação em escala de 1 a 5.

## Privacidade e segurança

Os cenários atuais são sintéticos. O contexto enviado não inclui nome de
paciente, diagnóstico ou prontuário. Em uma implantação real, dados pessoais não
devem ser enviados sem base legal, controles institucionais e configuração
adequada do ambiente.

A chave da API deve existir somente na variável `OPENAI_API_KEY`. O arquivo
`.env` é ignorado pelo Git e `.env.example` não contém segredo.

## Execução local

O modo padrão não realiza chamada externa:

```bash
python scripts/gerar_conteudo_llm.py
```

Os arquivos ficam em `reports/llm` e registram provedor, implementação local,
versão do prompt e horário de geração.

## Execução com OpenAI

Configure a chave fora do repositório:

```bash
export OPENAI_API_KEY="sua-chave"
export OPENAI_MODEL="gpt-5.6"
python scripts/gerar_conteudo_llm.py --provider openai
```

As evidências externas ficam em `reports/llm/openai`, sem sobrescrever exemplos
locais. Essa execução utiliza a API e pode gerar custos; a suíte automatizada
nunca acessa a rede. Execute o procedimento completo em
[Validação final antes do vídeo](demonstracao-final.md).
