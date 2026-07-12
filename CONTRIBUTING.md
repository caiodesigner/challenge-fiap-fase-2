# Contribuição

## Preparação

```bash
make install
```

O projeto exige Python 3.12. Dependências devem ser declaradas no
`pyproject.toml`; não instale bibliotecas apenas no ambiente local.

## Antes de enviar alterações

Execute o pipeline completo:

```bash
make check
```

O comando verifica:

- integridade das dependências;
- lint e formatação com Ruff;
- tipagem estática estrita com mypy;
- testes e cobertura com Pytest.

O limite mínimo global é 90% de cobertura de linhas e branches combinadas. Uma
alteração não deve aumentar a cobertura apenas com testes superficiais; priorize
regras, erros, limites e integração entre componentes.

## Convenções

- Use type hints em todo código de produção.
- Mantenha funções pequenas e responsabilidades separadas.
- Prefira entidades imutáveis para resultados e configurações.
- Não envie segredos, `.env`, dados pessoais ou dados clínicos.
- Preserve seeds nos experimentos para permitir reprodução.
- Não permita que a LLM altere resultados calculados pelo otimizador.
- Atualize documentação e testes junto de mudanças de comportamento.

## Estrutura de testes

Os testes acompanham as áreas do pacote:

```text
tests/
├── api/
├── application/
├── domain/
├── genetic/
├── llm/
├── optimization/
└── visualization/
```

Testes HTTP usam transporte ASGI e não abrem portas. Testes da LLM usam
provedores determinísticos e não fazem chamadas externas.

## Commits

Use mensagens curtas, no imperativo e focadas em uma mudança coerente. Não
inclua caches, ambientes virtuais ou relatórios temporários.
