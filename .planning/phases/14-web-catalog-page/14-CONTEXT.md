# Phase 14: Web Catalog Page - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Página web de catálogo no frontend Next.js existente (`frontend/`), onde qualquer pessoa pode navegar e filtrar o catálogo de raquetes disponíveis no Brasil. A página consome a Catalog API da Phase 13 e exibe os resultados em grid com filtros dinâmicos. Criar perfis de usuário, recomendações por IA e comparador avançado são fases separadas.

</domain>

<decisions>
## Implementation Decisions

### Stack & Localização
- **Next.js 14 + TypeScript** — construir no frontend existente em `frontend/`, NÃO Jinja2 (decisão de STATE.md está desatualizada)
- **Nova rota**: `frontend/app/catalog/page.tsx` — URL dedicada `/catalog`, não substitui a home existente
- **Tailwind CSS** já configurado — usar design tokens existentes (ver `tailwind.config.js`)
- **Dark mode já implementado**: bg `#000000`, accent `#ceff00` (lime), muted `#111111`, border `#222222`

### Dinamismo dos Filtros (WEB-03)
- **React state + fetch com debounce ~400ms** — cada mudança de filtro dispara fetch para `/catalog/paddles` após pausa de 400ms (não htmx — React/Next.js usa fetch nativo)
- **URL reflete filtros ativos** via `useSearchParams` + `useRouter` — links compartilháveis, botão voltar funciona, SEO-friendly (ex: `/catalog?brand=Joola&core_thickness=16`)
- **Auto-aplicar ao mudar** — sem botão "Filtrar" explícito; experiência fluida tipo Airbnb
- **Skeleton cards durante carregamento** — cards cinzas pulsando no lugar dos resultados (CSS animation, sem biblioteca extra)

### Layout dos Cards
- **Grid responsivo**: 3 colunas em desktop, 2 em tablet, 1 em mobile
- **Informações por card**: Foto da raquete + Nome + Marca (badge) + Espessura (badge) + Preço a partir de + Botão "Ver na [Loja]"
- **Specs técnicas** (espessura, material) como badges discretos sobre/abaixo do nome — já implementado no `paddle-card.tsx`
- **Raquetes sem imagem são filtradas** — apenas paddles com `image_url` preenchido aparecem no catálogo; filtro aplicado na query da API (`image_url IS NOT NULL`)
- **Botão "Ver na loja"**: label "Ver na [NomeDaLoja]" (ex: "Ver na ProPadel"), abre em nova aba (`target="_blank"`), usa a `url` do `MarketOffer` com menor preço

### Filtros Laterais/Drawer (WEB-02)
- **Filter drawer existente** (`filter-drawer.tsx`) é o padrão do projeto — bottom sheet no mobile
- **Filtros necessários**: espessura (14mm / 16mm), material da face (Carbon / Fiberglass), preço (range slider), marca (multi-select com busca), loja (select)
- O `filter-drawer.tsx` já tem: marca, preço, espessura — **adicionar**: material da face (surface_material) e loja (store slug)
- **Claude's Discretion**: layout desktop — sidebar fixa à esquerda vs. manter drawer para todos os tamanhos

### Visual / Estilo
- Paleta dark já configurada no `tailwind.config.js` — usar as classes existentes: `bg-background`, `text-primary` (`#ceff00`), `border-border`, `bg-muted`
- Seguir o padrão visual existente do `paddle-card.tsx` (glass-card, hover ring primary, framer-motion)
- Skeleton: `bg-muted animate-pulse` com mesma proporção dos cards reais

### Claude's Discretion
- Layout de filtros em desktop: sidebar fixa à esquerda (novo padrão) ou manter bottom drawer para todos os tamanhos
- Paginação vs. infinite scroll para o grid (a API suporta `limit`/`offset`)
- Ordenação padrão dos resultados (preço crescente recomendado)
- Estado vazio quando nenhuma raquete corresponde aos filtros

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos desta fase
- `.planning/REQUIREMENTS.md` §WEB-01, WEB-02, WEB-03 — critérios de aceite da página de catálogo

### Catalog API (fonte de dados)
- `.planning/phases/13-catalog-api/13-CONTEXT.md` — decisões de design da API: endpoints, campos de resposta, paginação, filtros disponíveis
- `app/api/endpoints/catalog.py` — implementação real: `GET /catalog/paddles` (parâmetros: `core_thickness`, `surface_material`, `price_min`, `price_max`, `brand`, `store`, `limit`, `offset`) e `GET /catalog/stores`

### Frontend existente (componentes a reutilizar/estender)
- `frontend/components/paddle/paddle-card.tsx` — card base a estender com botão "Ver na loja"
- `frontend/components/paddle/filter-drawer.tsx` — drawer de filtros a estender com `surface_material` e `store`
- `frontend/tailwind.config.js` — design tokens: cores (`primary: #ceff00`, `background: #000000`, `muted`, `border`), dark mode, sombras, border-radius

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `components/paddle/paddle-card.tsx`: card completo com imagem, brand badge, nome, espessura badge, power/control ratings, swing weight scale, preço em BRL, botão comparar — estender adicionando botão "Ver na loja" com URL do MarketOffer
- `components/paddle/filter-drawer.tsx`: bottom sheet drawer com marca (multi-select + busca), price range slider (R$ 0–4000), espessura (14mm/16mm) — adicionar surface_material e store
- `components/ui/`: Card, Button, Badge, Skeleton, Drawer, Separator — todos disponíveis via shadcn/ui
- `components/ui/empty-state.tsx`: componente de estado vazio já existe — reutilizar
- `framer-motion`: já instalado para animações de entrada dos cards (`initial={{ opacity: 0, y: 20 }}`)
- `@radix-ui/react-slider`: slider de preço já instalado e em uso

### Established Patterns
- **Fetch pattern**: client component com `useEffect` + `useState` para buscar dados da API FastAPI
- **URL state**: usar `useSearchParams` e `useRouter` do Next.js para sincronizar filtros com a URL
- **Dark-first**: todos os componentes assumem dark mode (`bg-background text-foreground`)
- **Glass cards**: `glass-card` + `hover:ring-2 hover:ring-primary/30` — padrão visual dos cards de raquete
- **Debounce**: implementar com `setTimeout`/`clearTimeout` ou `useDebouncedCallback` do `use-debounce` (se disponível)

### Integration Points
- Nova rota: `frontend/app/catalog/page.tsx` (Server Component para SSR inicial + Client Component para interatividade)
- API base URL: via variável de ambiente `NEXT_PUBLIC_API_URL`
- Endpoint principal: `${NEXT_PUBLIC_API_URL}/catalog/paddles` com query params dos filtros ativos
- Endpoint stores: `${NEXT_PUBLIC_API_URL}/catalog/stores` para popular o select de lojas
- Navegação: adicionar link `/catalog` na navegação existente (`bottom-nav.tsx` ou layout)

</code_context>

<specifics>
## Specific Ideas

- Cards sem imagem não aparecem — filtrar na query da API com `WHERE image_url IS NOT NULL` (ou parâmetro dedicado)
- Botão "Ver na loja" deve mostrar o nome da loja no label para contexto (ex: "Ver na ProPadel"), não apenas "Comprar"
- URL compartilhável: `/catalog?brand=Joola&core_thickness=16` deve carregar a página já filtrada (ler `searchParams` no Server Component)
- Preço exibido como "A partir de R$ X.XXX" (menor preço entre as ofertas ativas) — consistente com o que a API retorna

</specifics>

<deferred>
## Deferred Ideas

- Sidebar fixa de filtros no desktop (vs. drawer atual) — pode ser Phase 15+ se quiser layout two-column
- Comparador de raquetes na página de catálogo — `paddle-comparator.tsx` já existe, mas ativar no catálogo é funcionalidade nova
- Ordenação pelo usuário (por preço, por rating, por marca) — backlog
- Infinite scroll — a API suporta offset, mas paginação simples satisfaz WEB-01 inicialmente

</deferred>

---

*Phase: 14-web-catalog-page*
*Context gathered: 2026-03-21*
