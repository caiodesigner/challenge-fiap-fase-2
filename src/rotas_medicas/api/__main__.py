"""Inicialização local da API com Uvicorn."""

import os

import uvicorn


def main() -> None:
    """Executa o servidor com endereço configurável para local ou nuvem."""
    uvicorn.run(
        "rotas_medicas.api.app:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
