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

- `OllamaProvider`: integração real com uma LLM executada localmente;
- `QueueProvider`: respostas controladas para testes;
- `RuleBasedProvider`: demonstração local, explicitamente sem LLM externa.

## Ollama e Qwen 2.5

O modelo escolhido é `qwen2.5:1.5b`. Ele é compacto, multilíngue, inclui
português e suporta saída estruturada. O Ollama executa o modelo sem cobrança
por chamada e expõe uma API HTTP local.

O adaptador envia o JSON Schema gerado pelo Pydantic no campo `format`:

```python
response = client.post(
    "/api/chat",
    json={
        "model": model,
        "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        ],
        "format": response_model.model_json_schema(),
        "stream": False,
    },
)
```

O conteúdo retornado é validado novamente com `model_validate_json`. O modelo e
o host podem ser alterados por `OLLAMA_MODEL` e `OLLAMA_HOST`.

Referências oficiais:

- [Structured outputs do Ollama](https://docs.ollama.com/capabilities/structured-outputs)
- [Qwen 2.5 no Ollama](https://ollama.com/library/qwen2.5:1.5b)

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

A LLM produz `DriverGuidance` escolhendo focos operacionais dentro de um conjunto
fechado e fundamentado. O sistema transforma essas escolhas em texto e combina a
orientação com o cromossomo final para montar `DriverInstructions`. Assim, o
modelo não pode inventar capacidades, velocidades ou metas, e veículos, IDs,
destinos e sequência das paradas nunca são controlados por ele.

### Relatório

O sistema avalia os três baselines e seleciona o plano viável de menor fitness.
Em seguida, calcula distância, custo, tempo estimado e veículos para a solução
genética e a referência. Economias absolutas e percentuais são anexadas ao
`EfficiencyReport` como `EfficiencyComparison`.

A LLM recebe esses dados para propor sugestões em `EfficiencyNarrative`. Os
riscos conhecidos, o resumo, os destaques numéricos, a interpretação e a
comparação finais são montados deterministicamente com os cálculos do sistema.
Assim, o texto final não pode substituir ou contradizer as métricas. Valores
negativos são apresentados como piora.

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

Como o Ollama é local, nenhuma chave ou conteúdo de rota é enviado a um serviço
externo. O arquivo `.env` continua ignorado para configurações locais.

## Execução local

O fallback determinístico não realiza inferência de LLM:

```bash
python scripts/gerar_conteudo_llm.py --provider local
```

Os arquivos ficam em `reports/llm` e registram provedor, implementação local,
versão do prompt e horário de geração.

## Execução com Ollama

Instale o Ollama, baixe o modelo uma vez e gere a evidência:

```bash
ollama pull qwen2.5:1.5b
python scripts/gerar_conteudo_llm.py --provider ollama --scenarios pequeno
```

As evidências ficam em `reports/llm/ollama`, sem sobrescrever os exemplos do
fallback. A suíte automatizada simula a API HTTP e não exige o modelo. Execute o
procedimento completo em
[Validação final antes do vídeo](demonstracao-final.md).
