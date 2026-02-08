# 💰 SliceInsights - Plano de Monetização

> **Última Atualização**: Fevereiro 2026  
> **Mercado**: Brasil (BRL)  
> **Status**: MVP Pronto para Monetização

---

## 📊 Tipo de Produto

| Categoria | SliceInsights |
|:---|:---|
| **Tipo Principal** | 📊 Dashboard + Recomendação |
| **Secundário** | 🔗 Afiliados de E-commerce |
| **Nicho** | 🏓 Pickleball Brasil |
| **Diferencial** | Quiz inteligente + Market Intelligence |

> [!TIP]
> O modelo **híbrido** (afiliados + assinatura) é ideal para o estágio atual: gera receita imediata via afiliados enquanto constrói base para SaaS.

---

## 💵 Unit Economics

### Custos de Infraestrutura (Mensal)

| Componente | Custo | Tier |
|:---|---:|:---|
| **Vercel** (Frontend) | R$0 | Hobby Free |
| **Render** (Backend) | R$0 | Starter Free |
| **Neon** (PostgreSQL) | R$0 | Free Tier |
| **GitHub Actions** | R$0 | Free Tier |
| **Total Infra** | **R$0** | ✅ |

### Projeção de Receita (Afiliados)

```
Visitantes/Mês: 1.000 → 10.000 (12 meses)
Taxa de Clique: 15% (quiz completers)
Taxa de Conversão: 2-3%
Ticket Médio: R$500 (raquete intermediária)
Comissão Média: 5% (Amazon BR + ML)

Receita = Visitantes × 0.15 × 0.025 × 500 × 0.05
Mês 1:    1.000 × 0.15 × 0.025 × 500 × 0.05 = R$93,75
Mês 6:    5.000 × 0.15 × 0.025 × 500 × 0.05 = R$468,75
Mês 12:  10.000 × 0.15 × 0.025 × 500 × 0.05 = R$937,50
```

### Métricas Target

| Métrica | Target | Atual |
|:---|:---|:---|
| **CAC** | R$0 (orgânico) | ✅ R$0 |
| **LTV (afiliados)** | R$25/usuário | 🔄 A medir |
| **Margem Bruta** | >95% | ✅ 100% (infra R$0) |
| **LTV:CAC** | >3:1 | ✅ ∞ (CAC=0) |

---

## 🏷️ Estrutura de Tiers

### Fase 1: Gratuito + Afiliados (Atual)

```
┌─────────────────────────────────────────────────────────┐
│                    🆓 GRATUITO                          │
├─────────────────────────────────────────────────────────┤
│  ✅ Quiz de Recomendação (ilimitado)                    │
│  ✅ Catálogo completo (460+ raquetes)                   │
│  ✅ Market Intelligence (stats, segmentos)              │
│  ✅ Comparador (Battle Mode)                            │
│  ✅ Hidden Gems (custo-benefício)                       │
│  💰 Links de compra = Afiliados                         │
└─────────────────────────────────────────────────────────┘
```

### Fase 2: Pro (Roadmap - Q2 2026)

```
┌─────────────────────────────────────────────────────────┐
│               💎 PRO - R$29/mês                         │
├─────────────────────────────────────────────────────────┤
│  ✅ Tudo do Gratuito                                    │
│  🆕 Alertas de preço (queda de 10%+)                    │
│  🆕 Histórico de preços (gráfico 90 dias)               │
│  🆕 Exportar comparações (PDF)                          │
│  🆕 Recomendações personalizadas (salvas)               │
│  🆕 Suporte prioritário via WhatsApp                    │
└─────────────────────────────────────────────────────────┘
```

### Fase 3: API/Enterprise (Roadmap - Q4 2026)

```
┌─────────────────────────────────────────────────────────┐
│           🏢 ENTERPRISE - Sob Consulta                  │
├─────────────────────────────────────────────────────────┤
│  🆕 API de Recomendação (white-label)                   │
│  🆕 Dados de mercado em tempo real                      │
│  🆕 Integração com e-commerce parceiros                 │
│  🆕 Dashboard customizado                               │
│  🆕 SLA garantido + Suporte dedicado                    │
└─────────────────────────────────────────────────────────┘
```

---

## 📡 Canais de Distribuição

### Prioridade Alta (Custo Zero)

| Canal | Ação | Timeline |
|:---|:---|:---|
| **SEO** | Blog de conteúdo Pickleball | Contínuo |
| **YouTube** | Reviews + "Qual raquete escolher?" | Mês 2+ |
| **Reddit** | r/Pickleball, comunidades BR | Imediato |
| **WhatsApp** | Grupos de jogadores locais | Imediato |
| **Product Hunt** | Launch oficial | Mês 1 |

### Prioridade Média (Baixo Custo)

| Canal | Ação | Timeline |
|:---|:---|:---|
| **Instagram** | Reels educativos | Mês 2+ |
| **Parcerias** | Clubes e quadras de Pickleball | Mês 3+ |
| **Google Ads** | Teste com R$200/mês | Validação |

---

## 💳 Gateway de Pagamento

### Afiliados (Fase 1 - Ativo)

| Programa | Status | Comissão |
|:---|:---|:---|
| **Amazon BR** | ✅ Configurado | 1-10% |
| **Mercado Livre** | ✅ Configurado | 2-8% |
| **Shopee** | 🔄 Roadmap | 3-8% |

### Assinaturas (Fase 2 - Planejado)

| Gateway | Motivo | Status |
|:---|:---|:---|
| **Stripe** | Internacional + BR, fácil integração | 🎯 Escolhido |
| **Pix** | Desconto de 10% para pagamento único | 🔄 Planejado |

---

## 🔧 Implementação Técnica

### ✅ Já Implementado

| Feature | Arquivo | Status |
|:---|:---|:---|
| `AffiliateService` | [affiliate_service.py](file:///home/diego/Documentos/projetos/data-products/sliceinsights/app/services/affiliate_service.py) | ✅ Ativo |
| Transform URLs | Automático via API | ✅ |
| Amazon Tag | Via `AFFILIATE_AMAZON_TAG` | ⚙️ Configurar |
| ML Affiliate | Via `AFFILIATE_ML_ID` | ⚙️ Configurar |

### 🔄 Próximos Passos Técnicos

| Prioridade | Feature | Esforço |
|:---|:---|:---|
| **P0** | Configurar env vars de afiliado em produção | 10 min |
| **P0** | Verificar links funcionando no frontend | 30 min |
| **P1** | Adicionar tracking de cliques (`affiliate_clicks` table) | 2h |
| **P1** | Dashboard interno de receita afiliados | 4h |
| **P2** | Alertas de preço (scraper + notificação) | 8h |
| **P2** | Integração Stripe para assinatura Pro | 8h |

---

## 📈 Metas por Prazo

| Prazo | Meta | Estratégia | Status |
|:---|---:|:---|:---|
| **Semana 1** | Primeiro clique rastreado | Configurar `AFFILIATE_*` env vars | 🔄 |
| **Mês 1** | R$100 | 500 visitantes, 10 conversões afiliado | 🔜 |
| **Mês 3** | R$500 | 2.500 visitantes, SEO + YouTube | 🔜 |
| **Mês 6** | R$2.000 MRR | 50 Pro @ R$29 + afiliados | 🔜 |
| **Mês 12** | R$5.000 MRR | API Enterprise + 150 Pro | 🔜 |

---

## 📋 Checklist de Launch

### Imediato (Esta Semana)

- [ ] Configurar `AFFILIATE_AMAZON_TAG` em produção
- [ ] Configurar `AFFILIATE_ML_ID` em produção  
- [ ] Validar links de afiliado no frontend
- [ ] Cadastrar no Amazon Associates BR
- [ ] Cadastrar no Mercado Livre Affiliates

### Curto Prazo (30 dias)

- [ ] Criar tabela `affiliate_clicks` para tracking
- [ ] Implementar evento de clique no frontend
- [ ] Publicar no Product Hunt
- [ ] Primeiro post no blog de SEO
- [ ] Compartilhar em 5 grupos WhatsApp de Pickleball

### Médio Prazo (90 dias)

- [ ] Lançar tier Pro (R$29/mês)
- [ ] Integrar Stripe
- [ ] Dashboard de métricas de receita
- [ ] Histórico de preços (feature Pro)

---

## 🎯 Resumo Executivo

| Aspecto | Decisão |
|:---|:---|
| **Modelo Principal** | Afiliados (Amazon BR + ML) |
| **Modelo Futuro** | SaaS Freemium (R$29/mês) |
| **Custo Infra** | R$0 (free tiers) |
| **Gateway** | Stripe + Pix |
| **Primeiro Revenue** | Afiliados (semana 1) |
| **Meta Mês 1** | R$100 |
| **Meta Mês 12** | R$5.000 MRR |

---

> **Próximo Passo**: Execute `P0` - configure as variáveis de ambiente de afiliado em produção e valide os links funcionando.

```bash
# Produção (Render/Railway)
AFFILIATE_AMAZON_TAG=sliceinsights-20
AFFILIATE_ML_ID=seu_id_ml
```
