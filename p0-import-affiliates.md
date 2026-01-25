# P0 Implementation Plan: Import Calculator & Affiliate Links

## Overview

Este plano detalha a implementação das duas prioridades P0 do roadmap estratégico:
1. **Calculadora de Importação** - Simular custos de importação para raquetes internacionais
2. **Links de Afiliados** - Monetização via Amazon/Mercado Livre

**Project Type:** WEB (Frontend + Backend enhancements)

---

## Success Criteria

| Feature | Metric de Sucesso |
|---------|-------------------|
| Calculadora de Importação | Usuário vê custo estimado (frete + impostos) para qualquer raquete |
| Afiliados | URLs de lojas redirecionam para links de afiliado |

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Frontend | Next.js 15 + shadcn/ui | Consistência com stack existente |
| Backend | FastAPI (Python) | Já em uso, consistente |
| Affiliate URLs | Environment Variables | Seguro, configurável sem deploy |
| Import Calc | Client-side | Sem API externa, fórmulas fixas do governo |

---

## File Structure

```
frontend/
├── components/
│   └── import-calculator/
│       ├── import-calculator.tsx    # [NEW] Modal/Sheet com formulário
│       └── import-summary.tsx       # [NEW] Card de resultado
├── lib/
│   └── import-utils.ts              # [NEW] Fórmulas de cálculo
└── app/
    └── page.tsx                     # [MODIFY] Adicionar CTA

app/ (backend)
├── services/
│   └── affiliate_service.py         # [NEW] Transform store URLs
└── api/v1/
    └── paddles.py                   # [MODIFY] incluir affiliate_url

.env
└── AFFILIATE_AMAZON_TAG=...         # [NEW]
└── AFFILIATE_ML_ID=...              # [NEW]
```

---

## Task Breakdown

### PHASE 1: Foundation (Backend)

#### Task 1.1: Affiliate URL Service
- **Agent:** `backend-specialist`
- **Priority:** P0
- **Dependencies:** None
- **INPUT:** Store URL (ex: `https://amazon.com.br/dp/ABC123`)
- **OUTPUT:** Affiliate URL (ex: `https://amazon.com.br/dp/ABC123?tag=sliceinsights-20`)
- **VERIFY:** Unit test com URLs de Amazon e Mercado Livre

#### Task 1.2: Integrate Affiliate in Paddle Response
- **Agent:** `backend-specialist`
- **Priority:** P0
- **Dependencies:** 1.1
- **INPUT:** `GET /api/v1/paddles`
- **OUTPUT:** Cada paddle inclui `affiliate_url` se disponível
- **VERIFY:** Response JSON contém `affiliate_url`

---

### PHASE 2: Frontend

#### Task 2.1: Import Calculator Component
- **Agent:** `frontend-specialist`
- **Priority:** P0
- **Dependencies:** None
- **INPUT:** Preço da raquete em USD (ou BRL se internacional)
- **OUTPUT:** UI com estimativa de custo total (produto + frete + imposto)
- **VERIFY:** Componente renderiza, aceita input, mostra resultado

#### Task 2.2: Import Utils (Fórmulas)
- **Agent:** `frontend-specialist`
- **Priority:** P0
- **Dependencies:** 2.1
- **INPUT:** Valor do produto, peso, origem
- **OUTPUT:** Objeto com breakdown: { produto, frete, imposto, total }
- **VERIFY:** Teste unitário com valores conhecidos

#### Task 2.3: CTA na Home/Paddle Card
- **Agent:** `frontend-specialist`
- **Priority:** P1
- **Dependencies:** 2.1
- **INPUT:** Paddle com `available_in_brazil === false`
- **OUTPUT:** Botão "Calcular Importação" abre a calculadora
- **VERIFY:** Botão aparece apenas para raquetes internacionais

---

### PHASE 3: Integration

#### Task 3.1: Frontend consume affiliate_url
- **Agent:** `frontend-specialist`
- **Priority:** P0
- **Dependencies:** 1.2, 2.1
- **INPUT:** Paddle card link de loja
- **OUTPUT:** Link redireciona para affiliate_url
- **VERIFY:** Clique no "Comprar" abre URL com tag de afiliado

---

### PHASE X: Verification

- [ ] `python .agent/skills/vulnerability-scanner/scripts/security_scan.py .`
- [ ] `python .agent/skills/lint-and-validate/scripts/lint_runner.py .`
- [ ] `npm run build` (sem erros)
- [ ] Manual: Testar calculadora com valores reais
- [ ] Manual: Verificar links de afiliado no Network tab

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Fórmulas de imposto mudam | Documentar fonte (Receita Federal) e criar constantes editáveis |
| Amazon rejeita tag | Validar conta de afiliado antes de deploy |
| UX complexa | Manter calculadora simples (3 campos: preço, peso, origem) |

---

## Agent Assignment

| Agent | Tasks | Parallel? |
|-------|-------|-----------|
| `backend-specialist` | 1.1, 1.2 | Sequencial |
| `frontend-specialist` | 2.1, 2.2, 2.3, 3.1 | Parcial (2.1 → 2.2 → 2.3) |
| `test-engineer` | PHASE X | Após implementação |
