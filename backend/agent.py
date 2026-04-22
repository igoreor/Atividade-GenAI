"""
Agente Text-to-SQL com LangChain + Gemini 2.5 Flash.

Fluxo:
  1. Pergunta em linguagem natural
  2. LLM gera SQL (com contexto do schema)
  3. Guardrail: valida que é um SELECT
  4. Executa no SQLite
  5. LLM interpreta os resultados e responde em português
  Retry automático (até MAX_RETRIES) se o SQL falhar.
"""
import os
import re
import sqlite3
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.database import get_db_path, get_langchain_db

load_dotenv()

GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_ROWS: int = int(os.getenv("MAX_ROWS", "500"))
MAX_RETRIES: int = 3

# ---------------------------------------------------------------------------
# Guardrail — somente leitura
# ---------------------------------------------------------------------------
_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)
_WRITE_INTENT = re.compile(
    r"\b(apagar|deletar|remover|excluir|inserir|atualizar|modificar|alterar|criar|dropar)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> None:
    """Levanta ValueError se o SQL não for um SELECT puro."""
    clean = sql.strip().lstrip(";").strip()
    if not re.match(r"^\s*SELECT\b", clean, re.IGNORECASE):
        raise ValueError(f"Apenas consultas SELECT são permitidas. SQL recebido: {clean[:120]}")
    if _BLOCKED.search(clean):
        raise ValueError("SQL contém operação de escrita/DDL bloqueada pelo guardrail.")


def _check_user_intent(question: str) -> None:
    """Rejeita perguntas com intenção de escrita."""
    if _WRITE_INTENT.search(question):
        raise ValueError(
            "Esta API suporta apenas consultas de leitura. "
            "Operações de escrita não são permitidas."
        )


def _extract_sql(text: str) -> str:
    """Extrai o bloco SQL gerado pelo LLM (ignora markdown)."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # sem markdown — tenta pegar a partir do SELECT
    match = re.search(r"(SELECT\b.*)", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _run_sql(sql: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        rows = cur.fetchmany(MAX_ROWS)
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
_SQL_SYSTEM = """\
Você é um especialista em SQL para um banco de dados SQLite de e-commerce brasileiro.
Seu trabalho é converter perguntas em linguagem natural em consultas SQL corretas e eficientes.

REGRAS OBRIGATÓRIAS:
- Gere APENAS uma instrução SELECT. Nunca gere INSERT, UPDATE, DELETE, DROP, CREATE ou qualquer DDL/DML.
- Use apenas as tabelas e colunas listadas no schema abaixo.
- Sempre use LIMIT {max_rows} ao final, a menos que a pergunta peça um número específico menor.
- Para valores monetários, os campos estão em BRL (Real Brasileiro).
- Datas estão no formato ISO 8601 (YYYY-MM-DD HH:MM:SS).
- Responda SOMENTE com o bloco SQL, sem explicações.

SCHEMA DO BANCO:
{schema}

EXEMPLOS DE JOINS ÚTEIS:
- Produtos em pedidos: fat_itens_pedidos i JOIN dim_produtos p ON i.id_produto = p.id_produto
- Consumidor do pedido: fat_pedidos p JOIN dim_consumidores c ON p.id_consumidor = c.id_consumidor
- Avaliação do pedido: fat_pedidos p JOIN fat_avaliacoes_pedidos a ON p.id_pedido = a.id_pedido
- Vendedor do item: fat_itens_pedidos i JOIN dim_vendedores v ON i.id_vendedor = v.id_vendedor
- Total do pedido: use a view fat_pedido_total (já agrega valor total e frete por pedido)
"""

_SQL_HUMAN = "Pergunta: {question}"

_SQL_RETRY_HUMAN = """\
Pergunta: {question}

Tentativa anterior gerou o SQL abaixo que resultou em erro:
SQL: {previous_sql}
Erro: {error}

Corrija o SQL levando em conta o erro acima.
"""

_INTERPRET_SYSTEM = """\
Você é um analista de dados de e-commerce. Responda em português brasileiro de forma clara e objetiva.
Formate números monetários com prefixo R$ e separador de milhar.
Se os resultados forem uma lista, apresente de forma estruturada (tabela markdown ou lista numerada).
Se não houver dados, diga isso claramente.
Não mencione SQL na sua resposta ao usuário.
"""

_INTERPRET_HUMAN = """\
Pergunta original: {question}

Resultados da consulta ({row_count} linhas):
{results}

Responda a pergunta original com base nos resultados acima.
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
class TextToSQLAgent:
    def __init__(self) -> None:
        self._llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        self._sql_prompt = ChatPromptTemplate.from_messages([
            ("system", _SQL_SYSTEM),
            ("human", _SQL_HUMAN),
        ])
        self._sql_retry_prompt = ChatPromptTemplate.from_messages([
            ("system", _SQL_SYSTEM),
            ("human", _SQL_RETRY_HUMAN),
        ])
        self._interpret_prompt = ChatPromptTemplate.from_messages([
            ("system", _INTERPRET_SYSTEM),
            ("human", _INTERPRET_HUMAN),
        ])
        self._parser = StrOutputParser()

    def _schema_text(self) -> str:
        db = get_langchain_db()
        return db.get_table_info()

    def _generate_sql(self, question: str, previous_sql: str = "", error: str = "") -> str:
        schema = self._schema_text()
        if previous_sql:
            chain = self._sql_retry_prompt | self._llm | self._parser
            raw = chain.invoke({
                "schema": schema,
                "max_rows": MAX_ROWS,
                "question": question,
                "previous_sql": previous_sql,
                "error": error,
            })
        else:
            chain = self._sql_prompt | self._llm | self._parser
            raw = chain.invoke({
                "schema": schema,
                "max_rows": MAX_ROWS,
                "question": question,
            })
        return _extract_sql(raw)

    def _interpret(self, question: str, rows: list[dict], row_count: int) -> str:
        import json
        results_str = json.dumps(rows[:50], ensure_ascii=False, indent=2)
        chain = self._interpret_prompt | self._llm | self._parser
        return chain.invoke({
            "question": question,
            "row_count": row_count,
            "results": results_str,
        })

    def run(
        self,
        question: str,
        return_sql: bool = False,
    ) -> dict[str, Any]:
        """
        Executa o pipeline completo e retorna um dict com:
        - answer: str
        - sql: str | None
        - rows: list[dict]
        - row_count: int
        """
        _check_user_intent(question)

        sql = ""
        rows: list[dict] = []
        last_error = ""

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                sql = self._generate_sql(question, previous_sql=sql, error=last_error)
                _validate_sql(sql)
                rows = _run_sql(sql)
                break
            except (ValueError, sqlite3.Error) as exc:
                last_error = str(exc)
                if attempt == MAX_RETRIES:
                    return {
                        "answer": f"Não foi possível gerar uma consulta válida após {MAX_RETRIES} tentativas.",
                        "sql": sql if return_sql else None,
                        "rows": [],
                        "row_count": 0,
                        "error": last_error,
                    }

        answer = self._interpret(question, rows, len(rows))

        return {
            "answer": answer,
            "sql": sql if return_sql else None,
            "rows": rows,
            "row_count": len(rows),
            "error": None,
        }


# singleton reutilizável (inicializa LLM uma vez)
_agent_instance: TextToSQLAgent | None = None


def get_agent() -> TextToSQLAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = TextToSQLAgent()
    return _agent_instance
