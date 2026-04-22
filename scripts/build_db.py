"""
Constrói o banco de dados SQLite a partir dos CSVs da pasta dados/.
Execute uma única vez antes de iniciar a API:
    python scripts/build_db.py
"""
import os
import sqlite3
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(ROOT, "dados")
DB_PATH = os.path.join(ROOT, "banco.db")

TABLES = {
    "dim_consumidores": "dim_consumidores.csv",
    "dim_produtos": "dim_produtos.csv",
    "dim_vendedores": "dim_vendedores.csv",
    "dim_categoria_imagens": "dim_categoria_imagens.csv",
    "fat_pedidos": "fat_pedidos.csv",
    "fat_itens_pedidos": "fat_itens_pedidos.csv",
    "fat_avaliacoes_pedidos": "fat_avaliacoes_pedidos.csv",
}

FAT_PEDIDO_TOTAL_VIEW = """
CREATE VIEW IF NOT EXISTS fat_pedido_total AS
SELECT
    p.id_pedido,
    p.id_consumidor,
    p.status,
    p.pedido_compra_timestamp,
    p.pedido_entregue_timestamp,
    p.data_estimada_entrega,
    p.tempo_entrega_dias,
    p.tempo_entrega_estimado_dias,
    p.diferenca_entrega_dias,
    p.entrega_no_prazo,
    COALESCE(SUM(i.preco_BRL), 0)               AS total_produtos,
    COALESCE(SUM(i.preco_frete), 0)             AS total_frete,
    COALESCE(SUM(i.preco_BRL + i.preco_frete), 0) AS total_pedido,
    COUNT(i.id_item)                             AS quantidade_itens
FROM fat_pedidos p
LEFT JOIN fat_itens_pedidos i ON p.id_pedido = i.id_pedido
GROUP BY
    p.id_pedido,
    p.id_consumidor,
    p.status,
    p.pedido_compra_timestamp,
    p.pedido_entregue_timestamp,
    p.data_estimada_entrega,
    p.tempo_entrega_dias,
    p.tempo_entrega_estimado_dias,
    p.diferenca_entrega_dias,
    p.entrega_no_prazo
"""


def build(force: bool = False) -> str:
    if os.path.exists(DB_PATH) and not force:
        print(f"Banco já existe em {DB_PATH}. Use --force para recriar.")
        return DB_PATH

    conn = sqlite3.connect(DB_PATH)
    try:
        for table, csv_file in TABLES.items():
            path = os.path.join(CSV_DIR, csv_file)
            if not os.path.exists(path):
                print(f"  [AVISO] {csv_file} não encontrado — tabela '{table}' ignorada.")
                continue
            df = pd.read_csv(path)
            df.to_sql(table, conn, if_exists="replace", index=False)
            print(f"  OK {table:30s} {len(df):>7,} linhas")

        conn.execute(FAT_PEDIDO_TOTAL_VIEW)
        conn.commit()
        print(f"  OK view fat_pedido_total criada")
        print(f"\nBanco construído em: {DB_PATH}")
    finally:
        conn.close()

    return DB_PATH


if __name__ == "__main__":
    force = "--force" in sys.argv
    build(force=force)
