"""
Price Monitoring Pipeline using dlt.

Captura snapshots diários de preços para detecção de quedas e alertas.
Integra com o scraper existente do Brazil Pickleball Store.
"""

import os
import dlt
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


# Configuração
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "brazil_pickleball_store.csv"


def get_paddle_mapping():
    """Busca o mapeamento de (brand, model) para paddle_id no banco."""
    db_url = os.getenv("DATABASE_URL_SYNC")
    if not db_url:
        return {}
    
    engine = create_engine(db_url)
    query = """
    SELECT p.id, b.name as brand_name, p.model_name
    FROM paddle_master p
    JOIN brands b ON p.brand_id = b.id
    """
    try:
        df = pd.read_sql(query, engine)
        # Criar chave normalizada para busca
        df['key'] = (df['brand_name'].str.lower() + "_" + df['model_name'].str.lower()).str.replace(" ", "_").replace("-", "_")
        return dict(zip(df['key'], df['id']))
    except Exception as e:
        print(f"❌ Erro ao buscar mapeamento: {e}")
        return {}


@dlt.source(name="price_snapshots")
def price_snapshots_source(paddle_map):
    """Source que lê dados do CSV gerado pelo scraper."""
    
    @dlt.resource(
        name="price_snapshots",
        write_disposition="append",  # Append para histórico
        primary_key=["paddle_id", "snapshot_date", "store_name"]
    )
    def price_snapshots():
        """Gera snapshots de preços a partir do CSV."""
        
        if not CSV_PATH.exists():
            print(f"⚠️ CSV não encontrado: {CSV_PATH}")
            print("   Execute primeiro: python scripts/scrape_brazil_store.py")
            return
        
        try:
            if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
                print(f"⚠️ Arquivo {CSV_PATH} não encontrado ou vazio. Pulando...")
                return
            df = pd.read_csv(CSV_PATH)
        except Exception as e:
            print(f"❌ Erro ao ler {CSV_PATH}: {e}")
            return
        snapshot_date = datetime.now().strftime("%Y-%m-%d")
        
        for _, row in df.iterrows():
            # Gerar chave para busca no mapa
            search_key = f"{row['brand_name'].lower()}_{row['model_name'].lower()}"
            search_key = search_key.replace(" ", "_").replace("-", "_")
            
            paddle_id = paddle_map.get(search_key)
            
            if not paddle_id:
                print(f"⚠️ Paddle não encontrado no DB: {row['brand_name']} {row['model_name']}")
                continue
            
            yield {
                "paddle_id": str(paddle_id),
                "store_name": row["store_name"],
                "price_brl": float(row["price_brl"]),
                "url": row["product_url"],
                "snapshot_date": snapshot_date,
                "captured_at": datetime.now().isoformat(),
                "currency": "BRL",
                "is_available": True
            }
    
    return price_snapshots


def run_pipeline():
    """Executa o pipeline de captura de preços."""
    
    # 1. Carregar mapeamento de IDs
    paddle_map = get_paddle_mapping()
    if not paddle_map:
        print("❌ Falha crítica: Mapeamento de paddles está vazio. Abortando.")
        return
    
    # 2. Configurar pipeline dlt
    db_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
    pipeline = dlt.pipeline(
        pipeline_name="price_history_sync",
        destination=dlt.destinations.postgres(credentials=db_url) if db_url else "postgres",
        dataset_name="price_data",
    )
    
    print(f"🚀 Iniciando pipeline para {len(paddle_map)} paddles mapeados...")
    
    # 3. Executar
    # Note: dlt irá criar/mapear para a tabela 'price_snapshots' automaticamente
    load_info = pipeline.run(price_snapshots_source(paddle_map))
    
    print("✅ Pipeline concluído!")
    print(f"   - Load info: {load_info}")
    
    return load_info


def detect_price_drops(threshold_pct: float = 10.0):
    """
    Detecta quedas de preço significativas comparando com o histórico.
    
    Args:
        threshold_pct: Percentual mínimo de queda para alertar
        
    Returns:
        Lista de produtos com queda de preço
    """
    import psycopg2
    
    conn = psycopg2.connect(os.getenv("DATABASE_URL_SYNC"))
    
    query = """
    WITH latest_prices AS (
        SELECT DISTINCT ON (ps.paddle_id, ps.store_name)
            ps.paddle_id,
            ps.store_name,
            ps.price_brl as current_price,
            ps.url as product_url,
            ps.snapshot_date as latest_date
        FROM price_data.price_snapshots ps
        ORDER BY ps.paddle_id, ps.store_name, ps.snapshot_date DESC
    ),
    previous_prices AS (
        SELECT DISTINCT ON (ps.paddle_id, ps.store_name)
            ps.paddle_id,
            ps.store_name,
            ps.price_brl as previous_price,
            ps.snapshot_date as previous_date
        FROM price_data.price_snapshots ps
        WHERE ps.snapshot_date < (SELECT MAX(snapshot_date) FROM public.price_snapshots)
        ORDER BY ps.paddle_id, ps.store_name, ps.snapshot_date DESC
    )
    SELECT 
        l.paddle_id,
        b.name as brand_name,
        pm.model_name,
        p.previous_price,
        l.current_price,
        ROUND(((p.previous_price - l.current_price) / p.previous_price * 100)::numeric, 1) as drop_pct,
        l.product_url,
        l.store_name
    FROM latest_prices l
    JOIN previous_prices p ON l.paddle_id = p.paddle_id AND l.store_name = p.store_name
    JOIN public.paddle_master pm ON l.paddle_id = pm.id::varchar
    JOIN public.brands b ON pm.brand_id = b.id
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
