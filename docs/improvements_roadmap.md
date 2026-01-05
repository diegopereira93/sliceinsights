# Roadmap de Melhorias - Niterói Raquetes

Documento de sugestões estratégicas para evolução do produto, focado em refinamento de algoritmo, experiência do usuário e qualidade de dados.

---

## ✅ Fase 1 - Concluída

### 1.1 Refinamento do Algoritmo (Data Science)
- [x] **Normalização de Escalas (Smart Scoring)** - Percentile Rank para métricas físicas
- [x] **Slider de Preferência Fina** - Mistura personalizável Power/Control
- [x] **Value Score (Custo-Benefício)** - Pontuação técnica / preço

### 1.2 UX/UI & Engajamento
- [x] **Modo Comparador ("Battle Mode")** - Seleção de 2 raquetes lado a lado
- [x] **Visualização de "Sensação de Peso"** - Régua visual baseada em Swing Weight
- [x] **Gráfico de Evolução de Preço** - Sparkline com histórico de preço

### 1.3 Qualidade de Dados
- [x] **Agente de Preenchimento (LLM)** - Enriquecimento das Top 50 raquetes

### 1.4 Engenharia & Performance
- [x] **Testes de Regressão** - Cobertura do `recommendation_engine.py`
- [x] **Cache de Recomendações** - Redis/In-Memory para perfis comuns

---

## ✅ Fase 2 - Página de Estatísticas (Concluída)

Melhorias focadas na página `/statistics` transformando-a em um **hub de inteligência de mercado**.

### 2.1 Navegação e Hierarquia Visual

| Prioridade | Item | Status |
|------------|------|--------|
| P1 | [x] **Tabs de Navegação** | Overview / Comparativos / Rankings / Marcas |
| P2 | [ ] **Seções Colapsáveis** | Opcional - acordions para foco |
| P3 | [ ] **Progress Indicator** | Opcional - indicador lateral |

### 2.2 Insights Dinâmicos (Alto Impacto)

| Prioridade | Item | Status |
|------------|------|--------|
| **P0** | [x] **KPIs Calculados Dinamicamente** | Melhor valor, Top Power, Insight de mercado |
| **P0** | [x] **Card "Joia Escondida"** | Auto-detecção de anomalias positivas |
| P1 | [x] **Comparador de Segmentos** | Cards Budget / Mid-Range / Premium |
| P1 | [x] **Anomaly Detector** | Integrado no Hidden Gems |

### 2.3 Interatividade dos Gráficos

| Prioridade | Item | Status |
|------------|------|--------|
| P1 | [x] **Filtros Rápidos** | Toolbar com marca, preço, núcleo + quick filters |
| P1 | [x] **Rich Tooltips** | Mini-card com specs no hover |
| P2 | [ ] **Legenda Interativa** | Opcional |
| P3 | [ ] **Zoom/Pan nos Scatters** | Opcional |

### 2.4 Contexto e Educação do Usuário

| Prioridade | Item | Status |
|------------|------|--------|
| **P0** | [x] **Info Tooltips Técnicos** | Swing Weight, Twist Weight, Spin, Power, Control |
| P1 | [x] **Subtítulos "O que procurar"** | Dicas em cada seção |
| P2 | [ ] **Glossário Técnico** | Opcional - drawer com definições |

### 2.5 Brand Intelligence

| Prioridade | Item | Status |
|------------|------|--------|
| P1 | [x] **Posicionamento de Marcas** | Scatter preço vs performance |
| P2 | [x] **Radar Chart Comparativo** | Top 3 marcas |
| P2 | [x] **Especialização de Marca** | Tags automáticas (Power, Spin, Leve, Estável) |

### 2.6 Microinterações e Polish

| Prioridade | Item | Status |
|------------|------|--------|
| P2 | [x] **Animações de Entrada** | Framer Motion stagger nos KPIs |
| P2 | [ ] **Glow Effect no Hover** | Opcional |
| P3 | [ ] **Scroll-triggered Animations** | Opcional |

---

## 📦 Componentes Criados na Fase 2

| Componente | Caminho | Descrição |
|------------|---------|-----------|
| `InfoTooltip` | `components/ui/info-tooltip.tsx` | Tooltips para termos técnicos com definições pré-configuradas |
| `MarketSegments` | `components/statistics/market-segments.tsx` | Cards de segmentos Budget/Mid-Range/Premium |
| `HiddenGems` | `components/statistics/hidden-gems.tsx` | Detector automático de raquetes com ótimo custo-benefício |
| `ScatterFiltersToolbar` | `components/statistics/scatter-filters.tsx` | Toolbar de filtros para gráficos |
| `BrandIntelligence` | `components/statistics/brand-intelligence.tsx` | Análise de marcas com scatter e radar |
| `Tabs` | `components/ui/tabs.tsx` | Componente de navegação por abas |
| `Select` | `components/ui/select.tsx` | Dropdown de seleção |
| `Tooltip` | `components/ui/tooltip.tsx` | Tooltip básico Radix |

---

## 📐 Layout Implementado - Página de Estatísticas

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER + TABS [Overview] [Comparativos] [Rankings] [Marcas]│
├─────────────────────────────────────────────────────────────┤
│ QUICK INSIGHTS (4 cards dinâmicos)                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ │ 📊 Total │ │ 💰 Preço │ │ 💎 Best  │ │ ⚡ Top   │        │
│ │   Dados  │ │   Médio  │ │  Value   │ │  Power   │        │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
├─────────────────────────────────────────────────────────────┤
│ MARKET INSIGHT (Card com padrão de mercado)                │
├─────────────────────────────────────────────────────────────┤
│ HIDDEN GEMS (Top 5 joias escondidas clicáveis)             │
├─────────────────────────────────────────────────────────────┤
│ MARKET SEGMENTS                                             │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│ │   BUDGET   │ │  MID-RANGE │ │  PREMIUM   │               │
│ │  <R$800    │ │ R$800-1500 │ │  >R$1500   │               │
│ └────────────┘ └────────────┘ └────────────┘               │
├─────────────────────────────────────────────────────────────┤
│ TECHNICAL SPECS (Core Thickness, Handle, Brands)           │
├─────────────────────────────────────────────────────────────┤
│ DISTRIBUTIONS (Preço, Swing Weight, Twist Weight)          │
├─────────────────────────────────────────────────────────────┤
│ [Tab: Comparativos]                                         │
│ SCATTER FILTERS + 4 SCATTER CHARTS                         │
├─────────────────────────────────────────────────────────────┤
│ [Tab: Rankings]                                            │
│ LEADERBOARDS (Power, Spin, Swing, Twist)                   │
├─────────────────────────────────────────────────────────────┤
│ [Tab: Marcas]                                              │
│ BRAND INTELLIGENCE (Scatter + Radar + Tags)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Próximos Passos (Fase 3 - Sugestões)

### 3.1 Performance & Escalabilidade
- [ ] **Virtualização de listas longas** - react-window para leaderboards grandes
- [ ] **Lazy loading de gráficos** - Carregar charts apenas quando visíveis
- [ ] **SSG para estatísticas** - Pre-render de dados agregados

### 3.2 Funcionalidades Avançadas
- [ ] **Export de dados** - CSV/PDF das análises
- [ ] **Comparador personalizado** - Selecionar N raquetes para radar
- [ ] **Alertas de preço** - Notificar quando raquete favorita baixar

### 3.3 Monetização
- [ ] **Seção premium** - Análises exclusivas para assinantes
- [ ] **Links afiliados** - CTA de compra nos drawers
