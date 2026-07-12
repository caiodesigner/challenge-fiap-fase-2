# Checklist de entrega

## Repositório

- [x] Código-fonte completo.
- [x] Projeto Python estruturado com ambiente virtual documentado.
- [x] Cenários e contrato JSON.
- [x] Algoritmo genético especializado.
- [x] Prioridade, capacidade, autonomia e múltiplos veículos.
- [x] Baselines e experimentos reproduzíveis.
- [x] Mapas e indicadores.
- [x] Integração de LLM implementada.
- [x] API documentada por OpenAPI e guia Markdown.
- [x] Scripts de demonstração.
- [x] Testes automatizados.
- [x] CI no GitHub Actions.
- [x] Confirmar workflow verde após o commit final.

## Relatório técnico

- [x] Implementação do algoritmo genético.
- [x] Estratégias para restrições adicionais.
- [x] Integração com LLM e prompts.
- [x] Comparação com outras abordagens.
- [x] Visualizações e análise das rotas.
- [x] Desafios, soluções e limitações.
- [x] Arquitetura e decisões.
- [x] Resultados e reprodutibilidade.

## Demonstração da LLM

- [x] Modo local determinístico disponível.
- [x] Adaptador real Ollama implementado.
- [x] Qwen 2.5 pré-treinado selecionado.
- [x] JSON Schema e validação semântica.
- [x] Testes sem rede.
- [x] Comparação determinística com baseline no relatório.
- [x] Economia de distância, custo, tempo e veículos.
- [x] Script para registrar avaliação humana.
- [x] Baixar `qwen2.5:1.5b` no Ollama.
- [x] Executar e revisar uma amostra real do Ollama.
- [x] Registrar avaliação humana de clareza, utilidade e segurança.

A evidência real está em `reports/llm/ollama/pequeno.json`. A avaliação humana
aprovada, registrada por Caio, está em
`reports/llm/ollama/pequeno.avaliacao.json`. Os arquivos diretamente em
`reports/llm` permanecem identificados como exemplos do fallback determinístico.

## Vídeo

- [x] Roteiro de até 15 minutos preparado.
- [ ] Gravar demonstração do sistema.
- [ ] Mostrar componentes e arquitetura.
- [ ] Mostrar resultados do algoritmo genético.
- [ ] Demonstrar integração com LLM.
- [ ] Revisar áudio, imagem, duração e ausência de segredos.
- [ ] Fazer upload no YouTube ou Vimeo.
- [ ] Adicionar URL do vídeo ao README.

## Nuvem opcional

- [x] Decidir se o grupo buscará a pontuação extra de nuvem.
- [x] Containerizar a aplicação.
- [x] Criar IaC e documentação de implantação.
- [x] Adicionar health checks, observabilidade e gestão de segredos.
- [x] Adicionar validação da imagem e do Terraform no CI.
- [ ] Provisionar os recursos em um projeto Google Cloud autorizado.
- [ ] Registrar a URL e as evidências da implantação.

A configuração está completa e reproduzível. O provisionamento permanece manual
porque exige credenciais, faturamento e autorização do proprietário do projeto.

## Validação final

Executar em ambiente limpo:

```bash
make install
make check
python scripts/executar_experimentos.py --profile quick \
  --json-output /tmp/rotas-medicas-experimentos.json \
  --markdown-output /tmp/rotas-medicas-experimentos.md
python scripts/gerar_visualizacoes.py \
  --results /tmp/rotas-medicas-experimentos.json \
  --output-dir /tmp/rotas-medicas-visualizacoes
python scripts/gerar_conteudo_llm.py --provider ollama --scenarios pequeno \
  --output-dir /tmp/rotas-medicas-llm
python -m rotas_medicas.api
```

Os caminhos temporários evitam sobrescrever os resultados completos e a
evidência humana versionada durante um ensaio rápido.

Conferir:

- [ ] Interface abre em `http://127.0.0.1:8000`.
- [ ] Swagger abre em `/docs`.
- [ ] Cenário pequeno otimiza com seed 101.
- [ ] Mapa e métricas aparecem.
- [ ] Instruções, relatório e pergunta funcionam.
- [ ] Nenhum arquivo `.env` ou chave foi versionado.
- [ ] Worktree Git está limpo.

## Links a preencher

- Repositório: `https://github.com/caiodesigner/challenge-fiap-fase-2`
- Vídeo: **pendente**
- Implantação em nuvem: **configuração pronta; URL pendente de provisionamento**
