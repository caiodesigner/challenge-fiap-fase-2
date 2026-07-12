# Dados de demonstração

Esta pasta contém somente dados sintéticos, criados para validar o sistema sem
expor informações pessoais, clínicas ou operacionais reais.

## Cenários

| Arquivo | Entregas | Veículos | Resultado esperado |
|---|---:|---:|---|
| `cenario_pequeno.json` | 8 | 2 | Viável e inspecionável manualmente |
| `cenario_medio.json` | 30 | 5 | Viável para comparação de algoritmos |
| `cenario_critico.json` | 18 | 3 | Viável, com pouca folga e prioridades altas |
| `cenario_inviavel.json` | 6 | 2 | Inviável por carga indivisível excessiva |

Os arquivos obedecem ao contrato formal em `schema/cenario.schema.json`. A
unidade de carga adotada é `volume_logistico`, uma unidade abstrata que permite
comparar demanda e capacidade sem assumir quilogramas ou dimensões reais.

As coordenadas representam pontos fictícios próximos à cidade de São Paulo.
Nomes de unidades, destinos e cargas também são fictícios.

## Reprodução

Os quatro arquivos são gerados deterministicamente:

```bash
python scripts/gerar_cenarios.py
```

O comando sobrescreve apenas os arquivos `cenario_*.json` desta pasta. A seed e
os parâmetros de cada cenário ficam registrados no próprio arquivo.

