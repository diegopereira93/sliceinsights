"""
Seed híbrido: TODOS os dados para analytics + flag Brasil para catálogo
Run with: python -m app.db.seed_data_hybrid
"""
from pathlib import Path
from decimal import Decimal
from typing import Optional
import re

import pandas as pd
from sqlmodel import Session, select

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster, MarketOffer
from app.models.enums import FaceMaterial, PaddleShape

# Caminhos dos CSVs (relativos à raiz do projeto)
ROOT_DIR = Path(__file__).parent.parent.parent
INTERNATIONAL_CSV = ROOT_DIR / "data/raw/paddle_stats_dump.csv"
BRAZIL_STORE_CSV = ROOT_DIR / "data/raw/brazil_pickleball_store.csv"
JOOLA_BRAZIL_CSV = ROOT_DIR / "data/raw/joola_brazil.csv"

# Lista de fontes brasileiras para processar
BRAZILIAN_SOURCES = [
    (BRAZIL_STORE_CSV, "Brazil Pickleball Store"),
    (JOOLA_BRAZIL_CSV, "Joola Brazil")
]


def normalize_name(text):
    """Normalizar nome para comparação."""
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_brand_name(row_brand: str) -> str:
    """Clean brand name."""
    return str(row_brand).strip()


def infer_face_material(name: str) -> Optional[FaceMaterial]:
    """Try to infer face material from paddle name."""
    name_lower = name.lower()
    if "kevlar" in name_lower or "ruby" in name_lower:
        return FaceMaterial.KEVLAR
    if "fiberglass" in name_lower or "composite" in name_lower:
        return FaceMaterial.FIBERGLASS
    if "hybrid" in name_lower:
        return FaceMaterial.HYBRID
    if "carbon" in name_lower or "graphite" in name_lower:
        return FaceMaterial.CARBON
    return None


def infer_shape(name: str) -> Optional[PaddleShape]:
    """Try to infer shape from paddle name."""
    name_lower = name.lower()
    if "elongated" in name_lower or "blade" in name_lower:
        return PaddleShape.ELONGATED
    if "wide" in name_lower or "widebody" in name_lower or "quad" in name_lower:
        return PaddleShape.WIDEBODY
    if "standard" in name_lower or "classic" in name_lower:
        return PaddleShape.STANDARD
    return None


def normalize_rating(value) -> Optional[int]:
    """Normalize a value to an integer rating 0-10."""
    if pd.isna(value) or value == 0 or str(value).strip() in ["", "0", "nan"]:
        return None
    try:
        val_float = float(value)
        if val_float <= 10.0:
            return min(10, max(0, round(val_float)))
        if val_float > 100:
            score = (val_float - 150) / 10
            return min(10, max(0, round(score)))
        return min(10, max(0, round(val_float)))
    except (ValueError, TypeError):
        return None


def clean_price(price_val) -> Optional[Decimal]:
    """Clean price to Decimal."""
    if pd.isna(price_val):
        return None
    try:
        if isinstance(price_val, str):
            clean = re.sub(r'[^\d.]', '', price_val)
            if not clean:
                return None
            return Decimal(clean)
        return Decimal(str(price_val))
    except Exception:
        return None


def clean_float(val) -> Optional[float]:
    """Clean generic float value."""
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    try:
        return float(val)
    except Exception:
        return None


def clean_int(val) -> Optional[int]:
    """Clean generic int value."""
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    try:
        return int(float(val))
    except Exception:
        return None


def clean_str(val) -> Optional[str]:
    """Clean string value."""
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    return str(val).strip()


def clear_database(session: Session):
    """Limpar o banco de dados."""
    print("\n🗑️  Limpando banco de dados...")
    
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


def find_matching_specs(br_brand: str, br_model: str, int_dataset: pd.DataFrame) -> Optional[dict]:
    """
    Find matching paddle specs using SEMANTIC INTELLIGENT matching.
    
    Uses fuzzy string similarity + domain knowledge of paddle naming conventions.
    
    Tier 1: Exact match → 100%
    Tier 2: High fuzzy similarity (>70%) → 70-90%
    Tier 3: Semantic match (known variations) → 60-80%
    """
    from difflib import SequenceMatcher
    
    br_brand_norm = normalize_name(br_brand)
    br_model_norm = normalize_name(br_model)
    
    # Remove generic tokens for better matching
    GENERIC_TOKENS = {'mm', '14mm', '16mm', '13mm', '12mm', 'raquete', 'pickleball', 'paddle', 'de'}
    
    def clean_for_matching(text: str) -> str:
        """Remove generic tokens and normalize"""
        words = text.split()
        return ' '.join([w for w in words if w not in GENERIC_TOKENS])
    
    br_model_clean = clean_for_matching(br_model_norm)
    
    # Known aliases and variations in pickleball naming
    ALIASES = {
        'pro c': 'pro',
        'pro-c': 'pro',
        'wave pro': 'wave',
        'boomstik': 'boom stik',
        'enlongated': 'elongated',
        'widebody': 'wide',
        'jack sock': '',  # Remove player names for matching
        'anna bright': '',
        'ben johns': '',
        'tyson mcguffin': '',
        'simone jardim': '',
        'collin johns': '',
        'v3': '',  # Version numbers
        'v2': '',
        'regal': '',  # Edition names
        'limited': '',
        'edition': '',
        'especial': '',
        'sunset': '',
    }
    
    def apply_aliases(text: str) -> str:
        """Apply known aliases"""
        for old, new in ALIASES.items():
            text = text.replace(old, new)
        return ' '.join(text.split())  # Clean extra spaces
    
    br_model_aliased = apply_aliases(br_model_clean)
    
    best_match = None
    best_score = 0
    
    for _, row in int_dataset.iterrows():
        int_brand = normalize_name(row.get("Col_0", ""))
        int_model = normalize_name(row.get("Col_1", ""))
        
        # Skip if brand doesn't match
        if int_brand != br_brand_norm:
            continue
        
        int_model_clean = clean_for_matching(int_model)
        int_model_aliased = apply_aliases(int_model_clean)
        
        # Tier 1: Exact match (after cleaning/aliasing)
        if br_model_aliased == int_model_aliased:
            return {
                'row': row,
                'match_tier': 1,
                'match_score': 100,
                'match_method': 'exact_semantic'
            }
        
        # Tier 2: High fuzzy similarity (using SequenceMatcher)
        similarity = SequenceMatcher(None, br_model_aliased, int_model_aliased).ratio()
        
        if similarity >= 0.7:  # 70%+ similarity
            score = similarity * 100
            if score > best_score:
                best_score = score
                best_match = {
                    'row': row,
                    'match_tier': 2,
                    'match_score': score,
                    'match_method': 'fuzzy_semantic',
                    'matched_model': int_model
                }
        
        # Tier 3: Semantic partial matching (key terms present)
        # Extract key terms (longest words, likely model identifiers)
        br_terms = set([w for w in br_model_aliased.split() if len(w) >= 4])
        int_terms = set([w for w in int_model_aliased.split() if len(w) >= 4])
        
        if br_terms and int_terms:
            common_terms = br_terms.intersection(int_terms)
            if len(common_terms) >= 2:  # At least 2 significant terms
                overlap_ratio = len(common_terms) / max(len(br_terms), len(int_terms))
                score = overlap_ratio * 80  # Max 80 for partial
                
                if score > best_score and score >= 60:  # Minimum 60%
                    best_score = score
                    best_match = {
                        'row': row,
                        'match_tier': 3,
                        'match_score': score,
                        'match_method': 'semantic_partial',
                        'matched_model': int_model,
                        'common_terms': list(common_terms)
                    }
    
    return best_match


def seed_database_hybrid():
    """Seed híbrido v3: BR primeiro com specs enriquecidas via matching."""
    print("🌍🇧🇷 SliceInsights - Seed Híbrido v3")
    print("=" * 60)
    print("Estratégia: Matching inteligente para enriquecer specs BR")
    print("=" * 60)
    
    init_db_sync()
    
    import os
    force_clear = os.getenv("SEED_FORCE_CLEAR", "false").lower() == "true"
    
    with Session(sync_engine) as session:
        if force_clear:
            clear_database(session)
        else:
            print("\n⏭️  Pulando limpeza do banco (SEED_FORCE_CLEAR não é true)")
        
        
        brands_cache = {}
        paddles_created = {}  # {(brand_key, model_key): paddle_id}
        # FASE 1: Carregar dataset internacional em memória
        print("\n📊 Carregando dataset internacional para matching...")
        if not INTERNATIONAL_CSV.exists():
            print(f"❌ Arquivo não encontrado: {INTERNATIONAL_CSV}")
            return
        
        df_int = pd.read_csv(INTERNATIONAL_CSV)
        print(f"  📦 {len(df_int)} produtos carregados")
        
        # FASE 2: Criar produtos BR com specs enriquecidas (MÚLTIPLAS FONTES)
        matched_count = 0
        # skipped_count = 0  # Not used in this version
        tier_stats = {1: 0, 2: 0, 3: 0}
        
        for csv_path, source_name in BRAZILIAN_SOURCES:
            if not csv_path.exists():
                print(f"  ⏩ {source_name}: arquivo não encontrado, pulando...")
                continue
            
            print(f"\n🇧🇷 Processando: {source_name}")
            df_br = pd.read_csv(csv_path)
            print(f"  📦 {len(df_br)} produtos encontrados")
            
            for idx, row in df_br.iterrows():
                brand_name = str(row['brand_name']).strip().title()
                model_name = str(row['model_name']).strip()
                price_brl = clean_price(row['price_brl'])
                product_url = str(row['product_url'])
                store_name = str(row['store_name'])
                image_url = clean_str(row.get('image_url'))
                
                if not brand_name or not model_name:
                    continue
                
                # Criar/buscar marca
                if brand_name not in brands_cache:
                    brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
                    if not brand:
                        brand = Brand(name=brand_name, website="")
                        session.add(brand)
                        session.flush()
                    brands_cache[brand_name] = brand
                
                brand_obj = brands_cache[brand_name]
                
                # MATCHING: Buscar specs do dataset internacional
                match_result = find_matching_specs(brand_name, model_name, df_int)
                
                # Criar paddle brasileiro (COM ou SEM specs dependendo do match)
                keywords = [brand_name.lower(), model_name.lower()]
                
                if match_result:
                    # MATCH ENCONTRADO! Enriquecer com specs
                    matched_count += 1
                    tier_stats[match_result['match_tier']] += 1
                    
                    int_row = match_result['row']
                    
                    # Extrair specs do dataset internacional
                    power_rating = normalize_rating(int_row.get("Col_6"))
                    core_mm = clean_float(int_row.get("Col_7"))
                    
                    core_material_raw = clean_str(int_row.get("Col_14"))
                    face_material_raw = clean_str(int_row.get("Col_13"))
                    face_material = infer_face_material(str(face_material_raw)) if face_material_raw else infer_face_material(model_name)
                    if not face_material:
                        face_material_raw_2 = clean_str(int_row.get("Col_12"))
                        if face_material_raw_2:
                            face_material = infer_face_material(str(face_material_raw_2))
                    
                    shape = infer_shape(clean_str(int_row.get("Col_11")) or model_name)
                    swing_weight = clean_int(int_row.get("Col_3"))
                    twist_weight = clean_float(int_row.get("Col_4"))
                    spin_rpm = clean_int(int_row.get("Col_5"))
                    power_original = clean_float(int_row.get("Col_6"))
                    handle_length = clean_str(int_row.get("Col_8"))
                    grip_circumference = clean_str(int_row.get("Col_9"))
                    
                    if core_mm:
                        keywords.append(f"{int(core_mm)}mm")
                    
                    paddle = PaddleMaster(
                        brand_id=brand_obj.id,
                        model_name=model_name,
                        search_keywords=keywords,
                        image_url=image_url,
                        available_in_brazil=True,
                        # SPECS ENRIQUECIDAS do matching
                        core_thickness_mm=core_mm,
                        face_material=face_material,
                        core_material=core_material_raw,
                        shape=shape,
                        power_rating=power_rating,
                        swing_weight=swing_weight,
                        twist_weight=twist_weight,
                        spin_rpm=spin_rpm,
                        power_original=power_original,
                        handle_length=handle_length,
                        grip_circumference=grip_circumference,
                        specs_source=f"brazil_scraper+int_match_tier{match_result['match_tier']}",
                        specs_confidence=match_result['match_score'] / 100.0
                    )
                else:
                    # SEM MATCH: Criar apenas com dados básicos do scraper
                    paddle = PaddleMaster(
                        brand_id=brand_obj.id,
                        model_name=model_name,
                        search_keywords=keywords,
                        image_url=image_url,
                        available_in_brazil=True,
                        specs_source="brazil_scraper",
                        specs_confidence=1.0
                    )
                
                session.add(paddle)
                session.flush()
                
                # Guardar para evitar duplicatas
                brand_key = normalize_name(brand_name)
                model_key = normalize_name(model_name)
                paddles_created[(brand_key, model_key)] = paddle.id
                
                # Criar oferta brasileira
                if price_brl:
                    offer = MarketOffer(
                        paddle_id=paddle.id,
                        store_name=store_name,
                        price_brl=price_brl,
                        url=product_url
                    )
                    session.add(offer)
            
            session.commit()
            print(f"  ✅ {len(paddles_created)} produtos brasileiros criados")
            print(f"  🎯 {matched_count} com specs enriquecidas:")
            print(f"     Tier 1 (exact): {tier_stats[1]}")
            print(f"     Tier 2 (fuzzy): {tier_stats[2]}")
            print(f"     Tier 3 (partial): {tier_stats[3]}")
        
        # 2. ADICIONAR PRODUTOS INTERNACIONAIS (para analytics)
        print("\n📊 Adicionando produtos internacionais (analytics)...")
        if not INTERNATIONAL_CSV.exists():
            print(f"❌ Arquivo não encontrado: {INTERNATIONAL_CSV}")
            return
        
        df_int = pd.read_csv(INTERNATIONAL_CSV)
        print(f"  📦 {len(df_int)} produtos no dataset")
        
        int_created = 0
        int_skipped = 0
        
        for index, row in df_int.iterrows():
            raw_brand = row.get("Col_0")
            raw_model = row.get("Col_1")
            
            if pd.isna(raw_brand) or pd.isna(raw_model):
                continue
            
            brand_name = extract_brand_name(raw_brand)
            model_name = str(raw_model).strip()
            
            # Verificar se já existe (brasileiro)
            brand_key = normalize_name(brand_name)
            model_key = normalize_name(model_name)
            
            if (brand_key, model_key) in paddles_created:
                int_skipped += 1
                continue  # Pular, já criamos como BR
            
            # Criar/buscar marca
            if brand_name not in brands_cache:
                brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
                if not brand:
                    brand = Brand(name=brand_name, website="")
                    session.add(brand)
                    session.flush()
                brands_cache[brand_name] = brand
            
            brand_obj = brands_cache[brand_name]
            
            # Extrair specs do dataset internacional
            price = clean_price(row.get("Col_2"))
            power_rating = normalize_rating(row.get("Col_6"))
            core_mm = clean_float(row.get("Col_7"))
            
            core_material_raw = clean_str(row.get("Col_14"))
            face_material_raw = clean_str(row.get("Col_13"))
            face_material = infer_face_material(str(face_material_raw)) if face_material_raw else infer_face_material(model_name)
            if not face_material:
                face_material_raw_2 = clean_str(row.get("Col_12"))
                if face_material_raw_2:
                    face_material = infer_face_material(str(face_material_raw_2))
            
            shape = infer_shape(clean_str(row.get("Col_11")) or model_name)
            swing_weight = clean_int(row.get("Col_3"))
            twist_weight = clean_float(row.get("Col_4"))
            spin_rpm = clean_int(row.get("Col_5"))
            power_original = clean_float(row.get("Col_6"))
            handle_length = clean_str(row.get("Col_8"))
            grip_circumference = clean_str(row.get("Col_9"))
            
            keywords = [brand_name.lower(), model_name.lower()]
            if core_mm:
                keywords.append(f"{int(core_mm)}mm")
            
            # Criar paddle internacional (SEM imagem, para analytics)
            paddle = PaddleMaster(
                brand_id=brand_obj.id,
                model_name=model_name,
                search_keywords=keywords,
                core_thickness_mm=core_mm,
                face_material=face_material,
                core_material=core_material_raw,
                shape=shape,
                power_rating=power_rating,
                swing_weight=swing_weight,
                twist_weight=twist_weight,
                spin_rpm=spin_rpm,
                power_original=power_original,
                handle_length=handle_length,
                grip_circumference=grip_circumference,
                available_in_brazil=False,  # ← NÃO disponível no BR
                specs_source="international_dataset"
            )
            session.add(paddle)
            session.flush()
            int_created += 1
            
            # Adicionar oferta MSRP estimada
            if price:
                price_brl = price * Decimal("5.5")
                offer = MarketOffer(
                    paddle_id=paddle.id,
                    store_name="MSRP (Import)",
                    price_brl=price_brl,
                    url=f"https://example.com/search?q={brand_name}+{model_name.replace(' ', '+')}"
                )
                session.add(offer)
        
        session.commit()
        print(f"  ✅ {int_created} produtos internacionais adicionados")
        print(f"  ⏩ {int_skipped} pulados (já existem como BR)")
        
        # Estatísticas finais
        total_brands = len(session.exec(select(Brand)).all())
        total_paddles = len(session.exec(select(PaddleMaster)).all())
        brazilian_paddles = len(session.exec(select(PaddleMaster).where(
            PaddleMaster.available_in_brazil.is_(True)
        )).all())
        total_offers = len(session.exec(select(MarketOffer)).all())
        
        print("\n" + "=" * 60)
        print("🎉 Seed híbrido v2 completo!")
        print("\n📊 Totais no banco:")
        print(f"  🏷️  {total_brands} marcas")
        print(f"  🎾 {total_paddles} raquetes TOTAIS (analytics)")
        print(f"  🇧🇷 {brazilian_paddles} raquetes disponíveis no Brasil (catálogo COM IMAGENS)")
        print(f"  💰 {total_offers} ofertas de mercado")


if __name__ == "__main__":
    seed_database_hybrid()
