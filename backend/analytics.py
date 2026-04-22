"""
Consultas analíticas pré-definidas, cobrindo todos os exemplos do enunciado.
Cada entrada é um dict com: title, description, sql.
Execute via database.raw_query(entry["sql"]).
"""
from typing import TypedDict


class AnalyticsEntry(TypedDict):
    title: str
    description: str
    sql: str


ANALYTICS: dict[str, AnalyticsEntry] = {
    # ── Vendas e Receita ──────────────────────────────────────────────────
    "top-produtos": {
        "title": "Top 10 Produtos Mais Vendidos",
        "description": "Produtos com maior quantidade de unidades vendidas.",
        "sql": """
            SELECT
                p.nome_produto,
                p.categoria_produto,
                COUNT(i.id_item)           AS quantidade_vendida,
                ROUND(SUM(i.preco_BRL), 2) AS receita_total_BRL
            FROM fat_itens_pedidos i
            JOIN dim_produtos p ON i.id_produto = p.id_produto
            GROUP BY i.id_produto, p.nome_produto, p.categoria_produto
            ORDER BY quantidade_vendida DESC
            LIMIT 10
        """,
    },
    "receita-por-categoria": {
        "title": "Receita Total por Categoria de Produto",
        "description": "Soma do valor dos itens vendidos agrupada por categoria.",
        "sql": """
            SELECT
                p.categoria_produto,
                COUNT(DISTINCT i.id_pedido)  AS total_pedidos,
                COUNT(i.id_item)             AS itens_vendidos,
                ROUND(SUM(i.preco_BRL), 2)   AS receita_BRL,
                ROUND(AVG(i.preco_BRL), 2)   AS ticket_medio_item
            FROM fat_itens_pedidos i
            JOIN dim_produtos p ON i.id_produto = p.id_produto
            GROUP BY p.categoria_produto
            ORDER BY receita_BRL DESC
        """,
    },
    # ── Entrega e Logística ───────────────────────────────────────────────
    "pedidos-por-status": {
        "title": "Quantidade de Pedidos por Status",
        "description": "Distribuição dos pedidos pelos diferentes status.",
        "sql": """
            SELECT
                status,
                COUNT(*) AS quantidade,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentual
            FROM fat_pedidos
            GROUP BY status
            ORDER BY quantidade DESC
        """,
    },
    "prazo-por-estado": {
        "title": "% de Pedidos Entregues no Prazo por Estado do Consumidor",
        "description": "Percentual de entregas no prazo agrupado pelo estado do cliente.",
        "sql": """
            SELECT
                c.estado,
                COUNT(*)                                                              AS total_pedidos,
                SUM(CASE WHEN p.entrega_no_prazo = 'Sim' THEN 1 ELSE 0 END)         AS entregues_no_prazo,
                ROUND(
                    100.0 * SUM(CASE WHEN p.entrega_no_prazo = 'Sim' THEN 1 ELSE 0 END)
                    / COUNT(*), 2
                )                                                                     AS pct_no_prazo
            FROM fat_pedidos p
            JOIN dim_consumidores c ON p.id_consumidor = c.id_consumidor
            WHERE p.status = 'entregue'
            GROUP BY c.estado
            ORDER BY pct_no_prazo DESC
        """,
    },
    # ── Satisfação e Avaliações ───────────────────────────────────────────
    "media-avaliacao-geral": {
        "title": "Média Geral de Avaliação dos Pedidos",
        "description": "Nota média de satisfação consolidada.",
        "sql": """
            SELECT
                ROUND(AVG(avaliacao), 2)        AS media_geral,
                COUNT(*)                         AS total_avaliacoes,
                SUM(CASE WHEN avaliacao = 5 THEN 1 ELSE 0 END) AS nota_5,
                SUM(CASE WHEN avaliacao = 4 THEN 1 ELSE 0 END) AS nota_4,
                SUM(CASE WHEN avaliacao = 3 THEN 1 ELSE 0 END) AS nota_3,
                SUM(CASE WHEN avaliacao = 2 THEN 1 ELSE 0 END) AS nota_2,
                SUM(CASE WHEN avaliacao = 1 THEN 1 ELSE 0 END) AS nota_1
            FROM fat_avaliacoes_pedidos
        """,
    },
    "top-vendedores-avaliacao": {
        "title": "Top 10 Vendedores por Média de Avaliação",
        "description": "Melhores vendedores segundo a nota média dos clientes (mín. 10 avaliações).",
        "sql": """
            SELECT
                v.nome_vendedor,
                v.estado,
                COUNT(a.id_avaliacao)           AS total_avaliacoes,
                ROUND(AVG(a.avaliacao), 2)       AS media_avaliacao
            FROM fat_avaliacoes_pedidos a
            JOIN fat_pedidos p      ON a.id_pedido   = p.id_pedido
            JOIN fat_itens_pedidos i ON p.id_pedido  = i.id_pedido
            JOIN dim_vendedores v   ON i.id_vendedor = v.id_vendedor
            GROUP BY i.id_vendedor, v.nome_vendedor, v.estado
            HAVING COUNT(a.id_avaliacao) >= 10
            ORDER BY media_avaliacao DESC
            LIMIT 10
        """,
    },
    # ── Consumidores ──────────────────────────────────────────────────────
    "estados-volume-ticket": {
        "title": "Estados com Maior Volume de Pedidos e Ticket Médio",
        "description": "Ranking de estados por quantidade de pedidos e valor médio por pedido.",
        "sql": """
            SELECT
                c.estado,
                COUNT(DISTINCT pt.id_pedido)        AS total_pedidos,
                ROUND(AVG(pt.total_pedido), 2)       AS ticket_medio_BRL,
                ROUND(SUM(pt.total_pedido), 2)       AS receita_total_BRL
            FROM fat_pedido_total pt
            JOIN dim_consumidores c ON pt.id_consumidor = c.id_consumidor
            GROUP BY c.estado
            ORDER BY total_pedidos DESC
        """,
    },
    "estados-maior-atraso": {
        "title": "Estados com Maior Atraso na Entrega",
        "description": "Média de dias de atraso por estado do consumidor (apenas pedidos atrasados).",
        "sql": """
            SELECT
                c.estado,
                COUNT(*)                                  AS pedidos_atrasados,
                ROUND(AVG(p.diferenca_entrega_dias), 1)   AS atraso_medio_dias,
                ROUND(MAX(p.diferenca_entrega_dias), 1)   AS maior_atraso_dias
            FROM fat_pedidos p
            JOIN dim_consumidores c ON p.id_consumidor = c.id_consumidor
            WHERE p.entrega_no_prazo = 'Não'
              AND p.status = 'entregue'
              AND p.diferenca_entrega_dias > 0
            GROUP BY c.estado
            ORDER BY atraso_medio_dias DESC
        """,
    },
    # ── Vendedores e Produtos ─────────────────────────────────────────────
    "produtos-mais-vendidos-por-estado": {
        "title": "Produto Mais Vendido por Estado do Consumidor",
        "description": "Para cada estado, o produto com maior quantidade vendida.",
        "sql": """
            WITH ranked AS (
                SELECT
                    c.estado,
                    p.nome_produto,
                    p.categoria_produto,
                    COUNT(i.id_item) AS qtd,
                    ROW_NUMBER() OVER (
                        PARTITION BY c.estado ORDER BY COUNT(i.id_item) DESC
                    ) AS rn
                FROM fat_itens_pedidos i
                JOIN fat_pedidos pd    ON i.id_pedido   = pd.id_pedido
                JOIN dim_consumidores c ON pd.id_consumidor = c.id_consumidor
                JOIN dim_produtos p    ON i.id_produto  = p.id_produto
                GROUP BY c.estado, i.id_produto, p.nome_produto, p.categoria_produto
            )
            SELECT estado, nome_produto, categoria_produto, qtd AS quantidade_vendida
            FROM ranked
            WHERE rn = 1
            ORDER BY estado
        """,
    },
    "categorias-avaliacao-negativa": {
        "title": "Categorias com Maior Taxa de Avaliação Negativa",
        "description": "Categorias com maior proporção de notas 1 ou 2 (avaliações negativas).",
        "sql": """
            SELECT
                p.categoria_produto,
                COUNT(a.id_avaliacao)                                               AS total_avaliacoes,
                SUM(CASE WHEN a.avaliacao <= 2 THEN 1 ELSE 0 END)                  AS avaliacoes_negativas,
                ROUND(
                    100.0 * SUM(CASE WHEN a.avaliacao <= 2 THEN 1 ELSE 0 END)
                    / COUNT(a.id_avaliacao), 2
                )                                                                   AS pct_negativo,
                ROUND(AVG(a.avaliacao), 2)                                          AS media_nota
            FROM fat_avaliacoes_pedidos a
            JOIN fat_pedidos pd     ON a.id_pedido   = pd.id_pedido
            JOIN fat_itens_pedidos i ON pd.id_pedido = i.id_pedido
            JOIN dim_produtos p     ON i.id_produto  = p.id_produto
            GROUP BY p.categoria_produto
            HAVING COUNT(a.id_avaliacao) >= 50
            ORDER BY pct_negativo DESC
        """,
    },
}
