import pandas as pd
from sqlmodel import Session, select
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, Tuple

from app.models import PaddleMaster, Brand

class EnrichmentService:
    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or Path(__file__).parent.parent / "data" / "paddle_stats_dump.csv"
        self._df = None
        self._column_mapping = {
            0: 'brand',
            1: 'model',
            3: 'swing_weight',
            4: 'twist_weight',
            10: 'spin_rpm',
            7: 'core_thickness_mm',
            8: 'handle_length',
            9: 'grip_circumference'
        }

    @property
    def df(self):
        if self._df is None:
            if not self.csv_path.exists():
                raise FileNotFoundError(f"Technical dump not found at {self.csv_path}")
            self._df = pd.read_csv(self.csv_path, header=None)
            self._df = self._df.rename(columns=self._column_mapping)
            self._df['key'] = self._df['brand'].apply(self._normalize) + "|" + self._df['model'].apply(self._normalize)
        return self._df

    def _normalize(self, text: str) -> str:
        if not text: return ""
        return str(text).lower().strip()

    def find_match(self, brand_name: str, model_name: str) -> Tuple[Optional[pd.Series], float]:
        """Find best match for a paddle in the technical dump."""
        normalized_brand = self._normalize(brand_name)
        normalized_model = self._normalize(model_name)
        target_key = f"{normalized_brand}|{normalized_model}"
        
        # 1. Direct match
        direct_match = self.df[self.df['key'] == target_key]
        if not direct_match.empty:
            return direct_match.iloc[0], 1.0

        # 2. Fuzzy match within same brand
        brand_paddles = self.df[self.df['brand'].apply(self._normalize) == normalized_brand]
        if brand_paddles.empty:
            return None, 0.0

        best_score = 0
        best_match = None
        for _, row in brand_paddles.iterrows():
            score = SequenceMatcher(None, normalized_model, self._normalize(row['model'])).ratio()
            if score > best_score:
                best_score = score
                best_match = row

        return best_match, best_score

    def enrich_paddle(self, paddle: PaddleMaster, brand_name: str, force_overwrite: bool = False) -> bool:
        """Enrich a single paddle with technical specs."""
        match_row, score = self.find_match(brand_name, paddle.model_name)
        
        if match_row is None or score < 0.85:
            return False

        changes = False
        fields_to_enrich = [
            ('swing_weight', int),
            ('spin_rpm', int),
            ('twist_weight', float),
            ('core_thickness_mm', float),
            ('handle_length', str),
            ('grip_circumference', str)
        ]

        for field, dtype in fields_to_enrich:
            current_val = getattr(paddle, field)
            us_val = match_row[field]
            
            if pd.isna(us_val):
                continue

            is_placeholder = False
            if field == 'spin_rpm' and current_val is not None and current_val < 500:
                is_placeholder = True
            if field == 'swing_weight' and current_val is not None and current_val < 50:
                is_placeholder = True

            if current_val is None or current_val == 0 or is_placeholder or force_overwrite:
                try:
                    new_val = dtype(us_val)
                    if new_val != current_val:
                        setattr(paddle, field, new_val)
                        changes = True
                except (ValueError, TypeError):
                    continue

        if changes:
            sources = getattr(paddle, 'validation_sources', []) or []
            if "us_dump" not in sources:
                sources.append("us_dump")
                paddle.validation_sources = sources
        
        return changes

    def enrich_all(self, session: Session) -> int:
        """Enrich all paddles in the database."""
        paddles = session.exec(select(PaddleMaster)).all()
        brands = {b.id: b.name for b in session.exec(select(Brand)).all()}
        
        updated_count = 0
        for p in paddles:
            brand_name = brands.get(p.brand_id, "Unknown")
            if self.enrich_paddle(p, brand_name):
                updated_count += 1
        
        session.commit()
        return updated_count
