# Roadmap de Expansão do Catálogo

> **Conexão com Monetização**: Mais raquetes = mais oportunidades de afiliado = mais receita.

---

## Estado Atual

| Métrica | Valor |
|---------|-------|
| Raquetes | 5 |
| Marcas | 5 |
| Ofertas de Mercado | 10 |

---

## 1. Metas de Expansão

| Fase | Raquetes | Prazo | Trigger de Monetização |
|------|----------|-------|------------------------|
| MVP | 5 | ✅ Atual | Validação do fluxo |
| v1.0 | 25 | Mês 1 | Afiliados ativados |
| v1.5 | 50 | Mês 3 | Coverage de 80% do mercado BR |
| v2.0 | 100+ | Mês 6 | Dominância de busca orgânica |

---

## 2. Pipeline de Ingestão Automatizada

### 2.1 Arquitetura

```mermaid
graph LR
    A[Fontes de Dados] --> B[Scrapers/APIs]
    B --> C[Normalização]
    C --> D[Validação]
    D --> E[Upsert DB]
    E --> F[Gera Links Afiliado]
```

### 2.2 Fontes de Dados (Prioridade)

| Fonte | Tipo | Dados Obtidos | Automação |
|-------|------|---------------|-----------|
| Amazon BR | API/Scraper | Preço, ASIN, Disponibilidade | ⭐⭐⭐ Alta |
| Mercado Livre | API oficial | Preço, MLB ID | ⭐⭐⭐ Alta |
| Sites de Marcas | Scraper | Specs técnicas | ⭐⭐ Média |
| Pickleball Central | Scraper | Reviews, Ratings | ⭐ Baixa |

### 2.3 Script de Ingestão

```python
# scripts/catalog_ingestion.py

class CatalogIngestionPipeline:
    """Pipeline automatizado para expandir catálogo."""
    
    async def run(self):
        # 1. Buscar novos produtos
        new_products = await self.fetch_from_sources()
        
        # 2. Normalizar dados
        normalized = self.normalize(new_products)
        
        # 3. Enriquecer com specs (se faltando)
        enriched = await self.enrich_specs(normalized)
        
        # 4. Gerar ratings estimados (ML)
        rated = self.estimate_ratings(enriched)
        
        # 5. Upsert no banco
        await self.upsert_to_db(rated)
        
        # 6. Gerar links de afiliado
        await self.generate_affiliate_links()
```

---

## 3. Automação de Specs Técnicas

### 3.1 Problema
Specs técnicas (power, control, spin) não estão disponíveis em APIs de e-commerce.

### 3.2 Solução: Estimador ML

```python
# Modelo treinado com raquetes existentes
def estimate_ratings(paddle: dict) -> dict:
    """Estima ratings baseado em características físicas."""
    
    # Heurísticas baseadas em física do esporte
    rules = {
        "power": lambda p: 10 - (p["core_thickness_mm"] - 13) * 0.5,
        "control": lambda p: 5 + (p["core_thickness_mm"] - 13) * 0.5,
        "spin": lambda p: 8 if p["face_material"] == "Carbon" else 6,
    }
    
    return {k: min(10, max(1, int(fn(paddle)))) for k, fn in rules.items()}
```

### 3.3 Flag de Confiança

```python
class PaddleMaster(SQLModel):
    # ... campos existentes ...
    specs_source: str  # "manufacturer", "scraped", "estimated"
    specs_confidence: float  # 0.0 - 1.0
```

---

## 4. Marcas Prioritárias para Expansão

| Marca | Raquetes Populares | Prioridade |
|-------|-------------------|------------|
| **CRBN** | 1X, 2X, 3X | ⭐⭐⭐ Alta |
| **Paddletek** | Bantam, Tempest | ⭐⭐⭐ Alta |
| **Onix** | Evoke, Z5 | ⭐⭐⭐ Alta |
| **HEAD** | Radical, Gravity | ⭐⭐ Média |
| **ProKennex** | Pro Flight, Ovation | ⭐⭐ Média |
| **Gearbox** | CX14, GX6 | ⭐ Baixa |

---

## 5. GitHub Actions: Atualização Automática

```yaml
# .github/workflows/catalog-update.yml

name: Catalog Update
on:
  schedule:
    - cron: '0 6 * * *'  # Diário às 6h
  workflow_dispatch:

jobs:
  update-catalog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run ingestion pipeline
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          AMAZON_API_KEY: ${{ secrets.AMAZON_API_KEY }}
        run: python scripts/catalog_ingestion.py
      
      - name: Update affiliate links
        run: python scripts/update_affiliate_links.py
```

---

## 6. Checklist de Implementação

### Semana 1-2: Infraestrutura
- [ ] Criar `scripts/catalog_ingestion.py`
- [ ] Adicionar campos `specs_source`, `specs_confidence` no schema
- [ ] Implementar scraper Amazon BR

### Semana 3-4: Expansão v1.0
- [ ] Adicionar 20 raquetes manualmente (marcas prioritárias)
- [ ] Validar pipeline de afiliados com volume maior
- [ ] Configurar GitHub Action para updates diários

### Mês 2-3: Automação Full
- [ ] Implementar scraper Mercado Livre
- [ ] Treinar modelo de estimativa de ratings
- [ ] Atingir meta de 50 raquetes

---

## 7. Métricas de Sucesso

| Métrica | Meta Mês 1 | Meta Mês 3 |
|---------|-----------|-----------|
| Raquetes no catálogo | 25 | 50 |
| % com link afiliado | 100% | 100% |
| % specs automáticas | 50% | 80% |
| Atualização de preços | Diária | Diária |

---

> [!TIP]
> **Regra 80/20**: Foque nas 20 raquetes mais vendidas no Brasil. Elas representam 80% das buscas e conversões de afiliado.
