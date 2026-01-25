from app.db.database import sync_engine
from sqlalchemy import text

with sync_engine.connect() as conn:
    # Dropar tabelas na ordem correta
    conn.execute(text("DROP TABLE IF EXISTS market_offers CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS paddle_master CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS brands CASCADE"))
    conn.commit()
    print("✅ Tabelas removidas!")

# Agora recriar tudo
from app.db.database import init_db_sync
init_db_sync()
print("✅ Tabelas recriadas com nova estrutura!")
