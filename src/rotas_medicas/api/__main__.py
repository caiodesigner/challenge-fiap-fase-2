"""Inicialização local da API com Uvicorn."""

import uvicorn


def main() -> None:
    """Executa o servidor de desenvolvimento na porta 8000."""
    uvicorn.run(
        "rotas_medicas.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
