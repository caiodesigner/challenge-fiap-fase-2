# Validação final antes do vídeo

Sim, a demonstração deve ser executada antes da gravação. Isso permite corrigir
modelo, respostas ou interface sem consumir o tempo do vídeo.

## 1. Validar o projeto

Com o ambiente virtual ativo:

```bash
make check
python scripts/executar_experimentos.py --profile quick
python scripts/gerar_visualizacoes.py
python scripts/gerar_conteudo_llm.py --provider local --scenarios pequeno
```

Confirme que testes, relatórios e mapas são gerados sem erro.

## 2. Preparar e executar a LLM pré-treinada

Instale o Ollama seguindo a documentação do seu sistema. Com o serviço ativo,
baixe o modelo uma única vez e execute o cenário pequeno:

```bash
ollama pull qwen2.5:1.5b
python scripts/gerar_conteudo_llm.py \
  --provider ollama \
  --scenarios pequeno \
  --period diario
```

O resultado será salvo em `reports/llm/ollama/pequeno.json` e registrará
provedor, modelo, versão do prompt e horário.

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
  reports/llm/ollama/pequeno.json \
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
export LLM_PROVIDER=ollama
export OLLAMA_MODEL="qwen2.5:1.5b"
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
8. encerre o servidor.

## 5. Critério de prontidão

O projeto está pronto para gravação quando:

- `make check` está verde;
- a evidência informa `provider.name = ollama` e o modelo Qwen;
- a avaliação humana está aprovada;
- a comparação contém distância, custo, tempo e veículos;
- nenhuma informação sensível aparece em arquivos ou terminal visível;
- a sequência completa foi ensaiada dentro do limite do roteiro.
