# Validação final antes do vídeo

Sim, a demonstração deve ser executada antes da gravação. Isso permite corrigir
credenciais, modelo, respostas ou interface sem consumir o tempo do vídeo.

## 1. Validar o projeto

Com o ambiente virtual ativo:

```bash
make check
python scripts/executar_experimentos.py --profile quick
python scripts/gerar_visualizacoes.py
python scripts/gerar_conteudo_llm.py --provider local --scenarios pequeno
```

Confirme que testes, relatórios e mapas são gerados sem erro.

## 2. Executar uma LLM pré-treinada

A chave deve ficar somente no ambiente do terminal. Não a escreva em arquivo,
comando versionado, captura de tela ou gravação:

```bash
read -rsp "OPENAI_API_KEY: " OPENAI_API_KEY
export OPENAI_API_KEY
export OPENAI_MODEL="gpt-5.6"
python scripts/gerar_conteudo_llm.py \
  --provider openai \
  --scenarios pequeno \
  --period diario
unset OPENAI_API_KEY
```

O resultado será salvo separadamente em `reports/llm/openai/pequeno.json`. Ele
registra provedor, modelo, versão do prompt e horário, mas nunca a chave.

Revise no JSON:

- instruções cobrem todos os veículos, paradas e prioridades;
- relatório explica a comparação e não transforma pioras em economias;
- `comparison` contém números calculados pelo sistema;
- sugestões citam padrões observáveis nas métricas ou rotas;
- resposta em linguagem natural usa IDs válidos;
- não há diagnóstico, prescrição, dado pessoal ou afirmação inventada.

## 3. Registrar avaliação humana

Depois de ler a evidência, atribua notas reais de 1 a 5:

```bash
python scripts/avaliar_conteudo_llm.py \
  reports/llm/openai/pequeno.json \
  --clarity 5 \
  --usefulness 4 \
  --safety 5 \
  --grounding 5 \
  --decision aprovado \
  --notes "Instruções claras; comparação coerente com os dados calculados."
```

Não copie as notas do exemplo sem avaliar o conteúdo. Se a decisão for
`revisar`, ajuste prompt ou contrato, gere uma nova evidência e repita a
avaliação. O arquivo resultante termina em `.avaliacao.json`.

## 4. Ensaiar a interface usada no vídeo

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY="sua-chave-somente-neste-terminal"
python -m rotas_medicas.api
```

Na interface:

1. selecione o cenário pequeno;
2. execute a otimização;
3. confira mapa, carga, autonomia e métricas;
4. gere instruções;
5. gere relatório diário;
6. faça uma pergunta sobre veículos ou entregas;
7. confira `/docs`;
8. encerre o servidor e execute `unset OPENAI_API_KEY`.

## 5. Critério de prontidão

O projeto está pronto para gravação quando:

- `make check` está verde;
- a evidência informa `provider.name = openai`;
- a avaliação humana está aprovada;
- a comparação contém distância, custo, tempo e veículos;
- nenhuma chave aparece em arquivos ou terminal visível;
- a sequência completa foi ensaiada dentro do limite do roteiro.
