# app/main.py
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Importe o middleware
from routes import game_routes

app = FastAPI(
    title="Mesa de Bar API",
    description="API para gerenciar o jogo de discussão de ideias com IAs.",
    version="0.1.0"
)

# --- Bloco de configuração do CORS ---
# Lista de origens lida de CORS_ORIGINS (csv), com fallback para localhost.
# Permite que o operador altere via .env sem mexer no código.
_cors_default = "http://localhost:5173,http://127.0.0.1:5173"
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _cors_default).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Fim do Bloco do CORS ---

app.include_router(game_routes.router, prefix="/api", tags=["Game"])


@app.on_event("startup")
async def _log_catalog_on_startup():
    """Mostra no log do deploy a estrutura de temas/composições lida."""
    try:
        from catalog.catalog import summary_line
        print(summary_line())
    except Exception as e:  # nunca impedir o boot por causa do log
        print(f"[catálogo] não foi possível inspecionar a estrutura: {e}")

if __name__ == "__main__":
    print("Para desenvolvimento, execute o comando:")
    print("uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)