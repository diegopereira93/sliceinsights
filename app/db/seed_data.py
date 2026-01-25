"""
Seed script para popular o banco com dados de lojas brasileiras.
Run with: python -m app.db.seed_data
"""
from pathlib import Path
from decimal import Decimal

import pandas as pd
from sqlmodel import Session, select

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster, MarketOffer

# Caminhos dos CSVs brasileiros (absolutos dentro do container)
BRAZIL_STORE_CSV = Path("/app/data/raw/brazil_pickleball_store.csv")
MERCADO_LIVRE_CSV = Path("/app/data/raw/mercado_livre.csv")


def clean_brand_name(brand: str) -> str:
    """Limpar nome da marca."""
    return str(brand).strip().title()


def seed_from_csv(csv_path: Path, session: Session):
    """Processar um CSV de loja brasileira."""
    if not csv_path.exists():
        print(f"  ⚠️  CSV não encontrado: {csv_path}")
        return 0, 0
    
    print(f"\n📖 Processando {csv_path.name}...")
    df = pd.read_csv(csv_path)
    print(f"  📊 {len(df)} produtos encontrados")
    
    brands_cache = {}
    paddles_created = 0
    offers_created = 0
    
    for _, row in df.iterrows():
        try:
            # Extrair dados
            brand_name = clean_brand_name(row['brand_name'])
            model_name = str(row['model_name']).strip()
            price_brl = float(row['price_brl'])
            product_url = str(row['product_url'])
            image_url = str(row.get('image_url', ''))
            store_name = str(row['store_name'])
            
            # Pular se dados inválidos
            if not brand_name or not model_name or price_brl <= 0:
                continue
            
            # 1. Criar/buscar marca
            if brand_name not in brands_cache:
                brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
                if not brand:
                    brand = Brand(name=brand_name, website="")
                    session.add(brand)
                    session.flush()
                brands_cache[brand_name] = brand
            
            brand_obj = brands_cache[brand_name]
            
            # 2. Criar/buscar paddle
            paddle = session.exec(select(PaddleMaster).where(
                PaddleMaster.brand_id == brand_obj.id,
                PaddleMaster.model_name == model_name
            )).first()
            
            # Limpar image_url (converter vazios e 'nan' em None)
            clean_image = None
            if image_url and str(image_url).strip() and str(image_url).lower() not in ['nan', 'none', '']:
                clean_image = image_url
            
            if not paddle:
                paddle = PaddleMaster(
                    brand_id=brand_obj.id,
                    model_name=model_name,
                    search_keywords=[brand_name.lower(), model_name.lower()],
                    image_url=clean_image,
                    is_featured=False,
                    specs_source="brazil_scraper"
                )
                session.add(paddle)
                session.flush()
                paddles_created += 1
            elif not paddle.image_url and clean_image:
                # Atualizar imagem se não tiver
                paddle.image_url = clean_image
                session.add(paddle)
            
            # 3. Criar oferta de mercado
            offer = session.exec(select(MarketOffer).where(
                MarketOffer.paddle_id == paddle.id,
                MarketOffer.store_name == store_name,
                MarketOffer.url == product_url
            )).first()
            
            if not offer:
                offer = MarketOffer(
                    paddle_id=paddle.id,
                    store_name=store_name,
                    price_brl=Decimal(str(price_brl)),
                    url=product_url
                )
                session.add(offer)
                offers_created += 1
            else:
                # Atualizar preço se mudou
                offer.price_brl = Decimal(str(price_brl))
                session.add(offer)
        
        except Exception as e:
            print(f"  ⚠️  Erro ao processar linha: {e}")
            continue
    
    session.commit()
    return paddles_created, offers_created


def clear_database(session: Session):
    """Limpar o banco de dados (CUIDADO: remove todos os dados!)."""
    print("\n🗑️  Limpando banco de dados...")
    
    # Deletar na ordem correta (por causa de foreign keys)
    offers = session.exec(select(MarketOffer)).all()
    for offer in offers:
        session.delete(offer)
    
    paddles = session.exec(select(PaddleMaster)).all()
    for paddle in paddles:
        session.delete(paddle)
    
    brands = session.exec(select(Brand)).all()
    for brand in brands:
        session.delete(brand)
    
    session.commit()
    print("  ✅ Banco limpo!")


def seed_database():
    """Função principal para popular o banco com dados brasileiros."""
    print("🇧🇷 SliceInsights - Seed com Dados Brasileiros")
    print("=" * 50)
    
    # Garantir que as tabelas existem
    init_db_sync()
    
    with Session(sync_engine) as session:
        # LIMPAR BANCO (remover dados internacionais)
        clear_database(session)
        
        # Processar CSVs brasileiros
        total_paddles = 0
        total_offers = 0
        
        # Brazil Pickleball Store
        print(f"\n🔍 Verificando {BRAZIL_STORE_CSV}...")
        print(f"  Exists: {BRAZIL_STORE_CSV.exists()}")
        if BRAZIL_STORE_CSV.exists():
            paddles, offers = seed_from_csv(BRAZIL_STORE_CSV, session)
            total_paddles += paddles
            total_offers += offers
            print(f"  ✅ {paddles} raquetes | {offers} ofertas")
        else:
            print("  ❌ Arquivo não encontrado!")
        
        # Mercado Livre  
        print(f"\n🔍 Verificando {MERCADO_LIVRE_CSV}...")
        print(f"  Exists: {MERCADO_LIVRE_CSV.exists()}")
        if MERCADO_LIVRE_CSV.exists():
            paddles, offers = seed_from_csv(MERCADO_LIVRE_CSV, session)
            total_paddles += paddles
            total_offers += offers
            print(f"  ✅ {paddles} raquetes | {offers} ofertas")
        else:
            print("  ⚠️  Arquivo não encontrado (normal se não tiver Mercado Livre)")
        
        # Estatísticas finais
        print("\n" + "=" * 50)
        print("🎉 Seed completo!")
        print(f"  📦 {total_paddles} raquetes únicas criadas")
        print(f"  🛒 {total_offers} ofertas de lojas brasileiras")
        
        # Contar total no banco
        total_brands = session.exec(select(Brand)).all()
        total_paddles_db = session.exec(select(PaddleMaster)).all()
        total_offers_db = session.exec(select(MarketOffer)).all()
        
        print("\n📊 Totais no banco:")
        print(f"  🏷️  {len(total_brands)} marcas")
        print(f"  🎾 {len(total_paddles_db)} raquetes")
        print(f"  💰 {len(total_offers_db)} ofertas")


if __name__ == "__main__":
    seed_database()
