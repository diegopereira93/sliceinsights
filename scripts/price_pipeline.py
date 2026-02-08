"""
Price Monitoring Pipeline using dlt.

Captura snapshots diários de preços para detecção de quedas e alertas.
Integra com o scraper existente do Brazil Pickleball Store.
"""

import os
import dlt
from dlt.sources.helpers import requests
import pandas as pd
from datetime import datetime
from pathlib import Path


# Configuração
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "brazil_pickleball_store.csv"


@dlt.source(name="price_snapshots")
def price_snapshots_source():
    """Source que lê dados do CSV gerado pelo scraper."""
    
    @dlt.resource(
        name="price_snapshots",
        write_disposition="append",  # Append para histórico
        primary_key=["product_id", "snapshot_date"]
    )
    def price_snapshots():
        """Gera snapshots de preços a partir do CSV."""
        
        if not CSV_PATH.exists():
            print(f"⚠️ CSV não encontrado: {CSV_PATH}")
            print("   Execute primeiro: python scripts/scrape_brazil_store.py")
            return
        
        df = pd.read_csv(CSV_PATH)
        snapshot_date = datetime.now().strftime("%Y-%m-%d")
        
        for _, row in df.iterrows():
            # Gerar ID único para o produto
            product_id = f"{row['brand_name'].lower()}_{row['model_name'].lower()}"
            product_id = product_id.replace(" ", "_").replace("-", "_")[:100]
            
            yield {
                "product_id": product_id,
                "brand_name": row["brand_name"],
                "model_name": row["model_name"],
                "price_brl": float(row["price_brl"]),
                "product_url": row["product_url"],
                "store_name": row["store_name"],
                "snapshot_date": snapshot_date,
                "captured_at": datetime.now().isoformat(),
            }
    
    return price_snapshots


def run_pipeline():
    """Executa o pipeline de captura de preços."""
    
    # Configurar pipeline
    pipeline = dlt.pipeline(
        pipeline_name="price_monitoring",
        destination="postgres",
        dataset_name="price_data",
    )
    
    print("🚀 Iniciando pipeline de monitoramento de preços...")
    
    # Executar
    load_info = pipeline.run(price_snapshots_source())
    
    print(f"✅ Pipeline concluído!")
    print(f"   - Tabela: price_data.price_snapshots")
    print(f"   - Load info: {load_info}")
    
    return load_info


def detect_price_drops(threshold_pct: float = 10.0):
    """
    Detecta quedas de preço significativas.
    
    Args:
        threshold_pct: Percentual mínimo de queda para alertar
        
    Returns:
        Lista de produtos com queda de preço
    """
    import psycopg2
    
    conn = psycopg2.connect(os.getenv("DATABASE_URL_SYNC"))
    
    query = """
    WITH latest_prices AS (
        SELECT DISTINCT ON (product_id)
            product_id,
            brand_name,
            model_name,
            price_brl as current_price,
            product_url,
            snapshot_date as latest_date
        FROM price_data.price_snapshots
        ORDER BY product_id, snapshot_date DESC
    ),
    previous_prices AS (
        SELECT DISTINCT ON (product_id)
            product_id,
            price_brl as previous_price,
            snapshot_date as previous_date
        FROM price_data.price_snapshots
        WHERE snapshot_date < (SELECT MAX(snapshot_date) FROM price_data.price_snapshots)
        ORDER BY product_id, snapshot_date DESC
    )
    SELECT 
        l.product_id,
        l.brand_name,
        l.model_name,
        p.previous_price,
        l.current_price,
        ROUND(((p.previous_price - l.current_price) / p.previous_price * 100)::numeric, 1) as drop_pct,
        l.product_url
    FROM latest_prices l
    JOIN previous_prices p ON l.product_id = p.product_id
    WHERE l.current_price < p.previous_price * (1 - %s / 100)
    ORDER BY drop_pct DESC
    """
    
    try:
        df = pd.read_sql(query, conn, params=(threshold_pct,))
        return df.to_dict("records")
    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()
