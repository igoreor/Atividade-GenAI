"""
Modelos Pydantic para request/response da API.
"""
from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Pergunta em linguagem natural sobre os dados",
        examples=["Quais são os 10 produtos mais vendidos?"],
    )
    return_sql: bool = Field(
        False,
        description="Se True, inclui o SQL gerado na resposta",
    )


class QueryResponse(BaseModel):
    question: str
    answer: str
    sql: str | None = None
    rows: list[dict[str, Any]] | None = None
    row_count: int = 0
    error: str | None = None


class AnalyticsRow(BaseModel):
    label: str | None = None
    value: Any = None


class AnalyticsResponse(BaseModel):
    title: str
    description: str
    rows: list[dict[str, Any]]
    row_count: int
    sql: str


class SchemaResponse(BaseModel):
    tables: dict[str, list[str]]


class HealthResponse(BaseModel):
    status: str
    db_ok: bool
    model: str
