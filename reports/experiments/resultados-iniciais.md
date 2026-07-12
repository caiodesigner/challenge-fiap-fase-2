# Resultados iniciais dos experimentos

| Cenário | Abordagem | Configuração | Execuções | Viáveis | Custo médio | Desvio | Distância média (km) | Tempo médio (s) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| medio | algoritmo_genetico | balanceada | 3 | 3 | 7.463767 | 0.113858 | 103.955 | 2.0371 |
| medio | algoritmo_genetico | exploracao | 3 | 3 | 7.446300 | 0.068911 | 107.579 | 2.1102 |
| medio | algoritmo_genetico | explotacao | 3 | 3 | 7.838043 | 0.208179 | 117.154 | 2.0345 |
| medio | baseline | ordem_original | 1 | 1 | 12.117402 | 0.000000 | 88.788 | 0.0009 |
| medio | baseline | prioridade_distancia | 1 | 1 | 20.965635 | 0.000000 | 212.644 | 0.0017 |
| medio | baseline | vizinho_mais_proximo | 1 | 1 | 10.306886 | 0.000000 | 96.460 | 0.0050 |
| pequeno | algoritmo_genetico | balanceada | 3 | 3 | 1.274225 | 0.000000 | 17.009 | 0.2233 |
| pequeno | algoritmo_genetico | exploracao | 3 | 3 | 1.274370 | 0.000205 | 17.009 | 0.2365 |
| pequeno | algoritmo_genetico | explotacao | 3 | 3 | 1.274225 | 0.000000 | 17.009 | 0.2205 |
| pequeno | baseline | ordem_original | 1 | 1 | 1.823373 | 0.000000 | 17.359 | 0.0002 |
| pequeno | baseline | prioridade_distancia | 1 | 1 | 2.170371 | 0.000000 | 28.368 | 0.0003 |
| pequeno | baseline | vizinho_mais_proximo | 1 | 1 | 1.718520 | 0.000000 | 17.282 | 0.0002 |

## Leitura comparativa

- **medio:** `exploracao` obteve custo médio 7.446300, uma redução de 27.75% sobre o melhor baseline (`vizinho_mais_proximo`, 10.306886).
- **pequeno:** `balanceada` obteve custo médio 1.274225, uma redução de 25.85% sobre o melhor baseline (`vizinho_mais_proximo`, 1.718520).

Custos incluem penalidades de restrições. Por isso, resultados inviáveis não devem ser comparados apenas pela distância.
