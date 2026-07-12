.PHONY: install format lint type test check run experiments visualizations llm-demo llm-openai-demo container

PYTHON := .venv/bin/python

install:
	python3.12 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

format:
	$(PYTHON) -m ruff format .

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

type:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest

check: lint type test
	$(PYTHON) -m pip check

run:
	$(PYTHON) -m rotas_medicas.api

experiments:
	$(PYTHON) scripts/executar_experimentos.py

visualizations:
	$(PYTHON) scripts/gerar_visualizacoes.py

llm-demo:
	$(PYTHON) scripts/gerar_conteudo_llm.py

llm-openai-demo:
	@test -n "$(OPENAI_API_KEY)" || (echo "Defina OPENAI_API_KEY no ambiente." && exit 1)
	$(PYTHON) scripts/gerar_conteudo_llm.py --provider openai --scenarios pequeno

container:
	docker build -t rotas-medicas:local .
