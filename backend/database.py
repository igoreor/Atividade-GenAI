"""
Gerencia a conexão com o banco SQLite e expõe o schema ao agente.
"""
import os
import sqlite3
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

load_dotenv()

_DB_PATH: str = os.getenv("DB_PATH", "banco.db")


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, path)


def get_db_path() -> str:
    return _resolve_path(_DB_PATH)


@lru_cache(maxsize=1)
def get_langchain_db() -> SQLDatabase:
    path = get_db_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Banco não encontrado em '{path}'. "
            "Execute primeiro: python scripts/build_db.py"
        )
    return SQLDatabase.from_uri(
        f"sqlite:///{path}",
        sample_rows_in_table_info=3,
    )


def raw_query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Executa uma query SELECT e retorna lista de dicts."""
    path = get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_schema_info() -> dict[str, list[str]]:
    """Retorna {tabela: [colunas]} de todas as tabelas e views."""
    path = get_db_path()
    conn = sqlite3.connect(path)
    try:
        tables = conn.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table','view') ORDER BY type, name"
        ).fetchall()
        schema: dict[str, list[str]] = {}
        for name, kind in tables:
            cols = conn.execute(f"PRAGMA table_info('{name}')").fetchall()
            schema[name] = [f"{c[1]} ({c[2]})" for c in cols]
        return schema
    finally:
        conn.close()
