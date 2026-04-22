"""
FastAPI — E-Commerce Analytics Agent

Endpoints:
  GET  /health                              healthcheck
  GET  /schema                              schema do banco
  POST /query                               consulta em linguagem natural (text-to-SQL)
  GET  /analytics                           lista de análises disponíveis
  GET  /analytics/{slug}                    executa análise pré-definida

Análises pré-definidas (slug):
  top-produtos | receita-por-categoria | pedidos-por-status | prazo-por-estado
  media-avaliacao-geral | top-vendedores-avaliacao | estados-volume-ticket
  estados-maior-atraso | produtos-mais-vendidos-por-estado | categorias-avaliacao-negativa
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agent import get_agent
from backend.analytics import ANALYTICS
from backend.database import get_db_path, get_schema_info, raw_query
from backend.models import (
    AnalyticsResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SchemaResponse,
)

load_dotenv()

app = FastAPI(
    title="E-Commerce Analytics Agent",
    description=(
        "Agente Text-to-SQL para análise de dados de e-commerce. "
        "Powered by Gemini 2.5 Flash via LangChain."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
def health():
    """Verifica se a API e o banco estão operacionais."""
    db_ok = os.path.exists(get_db_path())
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_ok=db_ok,
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )


# ── Schema ────────────────────────────────────────────────────────────────────

@app.get("/schema", response_model=SchemaResponse, tags=["Sistema"])
def schema():
    """Retorna o schema completo do banco (tabelas e colunas)."""
    try:
        return SchemaResponse(tables=get_schema_info())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Text-to-SQL ───────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse, tags=["Agente"])
def query(req: QueryRequest):
    """
    Converte uma pergunta em linguagem natural em SQL, executa e interpreta.

    - `question`: pergunta em português sobre os dados
    - `return_sql`: se `true`, inclui o SQL gerado na resposta
    """
    try:
        agent = get_agent()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Agente indisponível: {exc}")

    try:
        result = agent.run(question=req.question, return_sql=req.return_sql)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro interno: {exc}")

    if result.get("error") and not result.get("rows"):
        raise HTTPException(status_code=422, detail=result["error"])

    return QueryResponse(
        question=req.question,
        answer=result["answer"],
        sql=result.get("sql"),
        rows=result["rows"],
        row_count=result["row_count"],
        error=result.get("error"),
    )


# ── Analytics pré-definidos ───────────────────────────────────────────────────

@app.get("/analytics", tags=["Analytics"])
def list_analytics():
    """Lista todas as análises pré-definidas disponíveis."""
    return [
        {"slug": slug, "title": entry["title"], "description": entry["description"]}
        for slug, entry in ANALYTICS.items()
    ]


@app.get("/analytics/{slug}", response_model=AnalyticsResponse, tags=["Analytics"])
def run_analytics(slug: str):
    """
    Executa uma análise pré-definida pelo slug.

    Slugs disponíveis:
    `top-produtos`, `receita-por-categoria`, `pedidos-por-status`,
    `prazo-por-estado`, `media-avaliacao-geral`, `top-vendedores-avaliacao`,
    `estados-volume-ticket`, `estados-maior-atraso`,
    `produtos-mais-vendidos-por-estado`, `categorias-avaliacao-negativa`
    """
    if slug not in ANALYTICS:
        raise HTTPException(
            status_code=404,
            detail=f"Análise '{slug}' não encontrada. "
                   f"Disponíveis: {list(ANALYTICS.keys())}",
        )

    entry = ANALYTICS[slug]
    try:
        rows = raw_query(entry["sql"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {exc}")

    return AnalyticsResponse(
        title=entry["title"],
        description=entry["description"],
        rows=rows,
        row_count=len(rows),
        sql=entry["sql"].strip(),
    )
