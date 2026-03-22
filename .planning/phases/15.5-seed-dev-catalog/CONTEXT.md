# Phase 15.5 Context

## Goal
Popular o DB dev com as 10 stores e paddles corretos para o frontend mostrar conteúdo.

## Problema Root Cause
- DB local tem 6 stores com nomes errados (Test Store, Pickleball Central, PB Village, Net2Court)
- Scrapers esperam: "Joola Brasil", "Shark", "Loja Supremo", "yoSports", "PCKL House", "ProPadel", "Just Paddles", "Brazil Pickleball Store", "Drop Shot Brasil", "ProSpin"
- Ao rodar scraper: `Store.name == STORE_NAME).one()` → `NoResultFound`
- docker-compose seed_v3 aponta `app.db.seed_brazil_catalog` (não existe)
- Frontend home → 0 paddles (dev vazio, prod tem 50)

## Decisões
| Decisão | Detalhes |
|---|---|
| Store names | Devolve dos scrapers (nome exato, não do compose) |
| Tech para justpaddles | Playwright async (já instalado no container) |
| Execução | Via docker exec (ambiente isolado com dependências) |

## Riscos
- Alguns scrapers podem falhar se as lojas mudaram layout
- JustPaddles usa `--ingest` flag nova
