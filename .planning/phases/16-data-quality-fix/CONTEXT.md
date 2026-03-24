---
phase: 16-data-quality-fix
created: 2026-03-23
---

## Contexto: Problemas Encontrados

### 1. Test data residual (5 paddles com fotos falsas)

5 paddles do antigo `seed_test_data.py` ainda estão no DB com fotos de Unsplash (pessoas aleatórias jogando tennis, não raquetes):

| UUID | Brand | Model | URL |
|------|-------|-------|-----|
| `88c7349f` | Selkirk | Invikta Air | unsplash.com/photo-1554068865 |
| `b6e3b220` | Joola | Scoop Alpha | unsplash.com/photo-1551698618 |
| `294b1891` | Onix | Perseus Pro | unsplash.com/photo-1584464491 |
| `e1629234` | Engage | Pursuit Pro | unsplash.com/photo-1535131749 |
| `cbf380dd` | Franklin | XLS Franklin | unsplash.com/photo-1558618666 |

**Ação:** DELETE these 5 paddles from DB, also delete their market_offers.

### 2. Brand name parsing errors (7 marcas quebradas)

Os scrapers fazem parsing ruim de nomes de marcas, criando "brands" que são na verdade parte de nomes de produtos:

| Brand atual | Problema | Ação |
|-------------|----------|------|
| `3Rdshot` | "3RDSHOT Venus" → brand="3Rdshot" | Renomear para "3RD Shot" |
| `Slk` | "SLK Era" → brand="Slk" | Renomear para "SLK" |
| `Com` | "Com 2 Raquetes..." → brand="Com" | DELETE brand, atualizar paddle brand_id |
| `Cs` | "Cs Pro Hyperlight..." → brand="Cs" | DELETE brand, atualizar paddle brand_id |
| `Boom` | "Starvie Boom" → brand="Boom" | Renomear para "Boom" ou unir com "Starvie" |
| `Pulse` | "Pulse Hyperlight" → brand="Pulse" | Renomear para "Pulse" |
| `Eagle` | "Eagle Pro Masasport" → brand="Eagle" | Renomear para "Eagle" |
| `Falcon` | "Falcon Pro Masasport" → brand="Falcon" | Renomear para "Falcon" |

### 3. Marcas com poucos paddles (ruim para UX)

Algumas marcas reais mas com apenas 1 paddle — podem ser dados de scraper ruins:

| Brand | Paddles | Ação |
|-------|---------|------|
| `Onix` | 1 | Verificar se é real — se não, deletar |
| `Starvie` | 1 | Verificar — pode ser "Starvie Boom" |
| `4X` | 1 | Verificar — pode ser real |
| `Paddletek` | 7 | Verificar se paddle é de loja brasileira |

### 4. Core thickness padrão incorreto

Vários paddles mostram "16mm" como padrão mas o valor real é diferente. UI está mostrando fallback hardcoded em vez do valor do DB.

## Impacto

- **UX:** Cards mostram fotos de pessoas aleatórias para 5 raquetes
- **UX:** Filtros por marca mostram "Com", "Cs", "Slk" — nomes quebrados
- **Data quality:** 7+ marcas com nomes errados

## Origem dos dados

- Dados reais: scrapers em `scripts/scrape_*.py` (10 lojas)
- Dados residuais: `seed_test_data.py` (antigo, não versionado)
- CSV seed: `data/db/paddle_master.csv`, `data/db/market_offers.csv`
