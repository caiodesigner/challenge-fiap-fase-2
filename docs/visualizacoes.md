# Visualizações

## Artefatos

A etapa de visualização transforma os resultados dos experimentos em quatro
formatos complementares:

- mapa HTML interativo;
- painel HTML de indicadores operacionais;
- GeoJSON das rotas e paradas;
- gráfico SVG de convergência.

Os arquivos são gerados para as melhores execuções genéticas viáveis dos
cenários pequeno e médio.

## Mapa interativo

O mapa usa Leaflet 1.9.4 e a camada pública do OpenStreetMap. Cada veículo recebe
uma cor de rota. As paradas apresentam:

- ordem de atendimento;
- destino fictício;
- veículo responsável;
- prioridade;
- demanda.

O depósito possui marcador próprio. A cor interna de cada entrega representa a
prioridade: crítica, alta, normal ou baixa. Um painel sobre o mapa resume
distância, fitness, veículos utilizados e viabilidade.

O HTML referencia Leaflet e os tiles via internet. Portanto, a visualização do
mapa-base requer conexão, embora todos os dados de rota estejam incorporados no
próprio arquivo.

## Painel de indicadores

O painel apresenta os indicadores gerais e uma tabela por veículo com:

- quantidade de entregas;
- carga absoluta e percentual da capacidade;
- distância e percentual da autonomia;
- custo operacional.

## GeoJSON

O GeoJSON permite reutilizar os resultados em ferramentas como QGIS, Kepler.gl
e aplicações web. A coleção contém pontos para depósito e entregas e uma
`LineString` para cada rota utilizada.

As linhas representam ligações diretas entre as coordenadas. Elas não simulam o
traçado real das ruas, pois o projeto usa distância Haversine nesta versão.

## Convergência

O gráfico SVG compara o melhor histórico de cada configuração genética. O eixo
horizontal representa gerações e o vertical, o menor custo encontrado. O SVG é
gerado somente com a biblioteca padrão do Python e pode ser incluído diretamente
no relatório técnico.

## Reprodução

Depois de executar os experimentos:

```bash
python scripts/gerar_visualizacoes.py
```

Para selecionar um cenário:

```bash
python scripts/gerar_visualizacoes.py --scenarios pequeno
```

Os artefatos são gravados em `reports/visualizations`.
