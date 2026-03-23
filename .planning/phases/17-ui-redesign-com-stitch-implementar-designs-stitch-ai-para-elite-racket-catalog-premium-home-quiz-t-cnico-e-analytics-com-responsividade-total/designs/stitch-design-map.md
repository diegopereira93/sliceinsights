# Stitch Design Map — Phase 17

> Note: Stitch MCP was unavailable during extraction. This document was generated using the fallback
> approach: design tokens from `tailwind.config.js` + `globals.css`, component inventory from
> existing source files, and the Stitch design prompts defined in 17-01-PLAN.md.
> When Stitch MCP becomes available, update the Per-Screen sections with extracted screenshots and HTML.

---

## Token Mapping (Stitch -> Project)

| Stitch Class       | Project Token              | Tailwind Class               | Value                     |
|--------------------|----------------------------|------------------------------|---------------------------|
| `bg-zinc-950`      | `bg-background`            | `bg-background`              | `#000000`                 |
| `bg-zinc-900`      | `bg-muted`                 | `bg-muted`                   | `#111111`                 |
| `border-zinc-800`  | `border-border`            | `border-border`              | `#222222`                 |
| `text-lime-400`    | `text-primary`             | `text-primary`               | `#ceff00`                 |
| `bg-lime-400`      | `bg-primary`               | `bg-primary`                 | `#ceff00`                 |
| `text-zinc-400`    | `text-muted-foreground`    | `text-muted-foreground`      | `#a1a1aa`                 |
| `text-white`       | `text-foreground`          | `text-foreground`            | `#ffffff`                 |
| `bg-white`         | `bg-secondary`             | `bg-secondary`               | `#ffffff`                 |
| `ring-lime-400`    | `ring-ring`                | `ring-ring`                  | `#ceff00`                 |
| `border-zinc-700`  | `border-input`             | `border-input`               | `#222222`                 |
| `bg-black/5`       | `.glass`                   | `.glass` (utility)           | `rgba(255,255,255,0.03) + blur(20px)` |
| `bg-white/5`       | `.glass-card`              | `.glass-card` (utility)      | `rgba(255,255,255,0.05) + blur(16px)` |
| `shadow-glow`      | `shadow-glow`              | `shadow-glow`                | `0 0 20px rgba(206,255,0,0.3)` |

---

## Stitch Design Prompts Used (Fallback)

These prompts were defined in 17-01-PLAN.md and represent the intended Stitch AI extractions:

- **Home:** `"Premium pickleball catalog page, dark theme (#000000 background, #ceff00 lime accent), glassmorphism cards, mobile-first, filtering sidebar"`
- **Quiz:** `"Multi-step recommendation wizard, 3 steps, dark theme, pill buttons for options, chat panel for AI results"`
- **Statistics:** `"Sports analytics dashboard, dark theme, scatter chart, tabs for overview/rankings/brands, badge-heavy data presentation"`

---

## Per-Screen Design Notes

### Home (/)

**Key design elements:**
- Hero section: dark background `bg-background` (#000000), lime accent heading with `.text-glow` utility
- Catalog grid: glassmorphism cards using `.glass-card` (backdrop blur, white/5 background, white/10 border)
- Search bar: full-width `<Input>` with `border-input` (#222222) and `bg-muted` (#111111)
- Filter sidebar/drawer: sticky panel with `bg-muted` background, `border-border` separator
- Brand badges: `<Badge>` components with `bg-primary` (#ceff00) accent on selection
- Bottom navigation: `pb-safe` padding for iOS safe area, `bg-muted` background
- Hover effects: `.glow-hover` — `translateY(-2px)` + `shadow-glow` on card hover
- Comparison bar: floating bar at bottom, `bg-primary` CTA button

**Responsive behavior:**
- Mobile: single column grid, collapsible filter drawer (full-screen overlay)
- Tablet: 2-column grid, filter panel side-drawer
- Desktop: 3-4 column grid, persistent filter sidebar

### Quiz (/recommend)

**Key design elements:**
- Multi-step wizard: 3 steps with progress indicator (step dots or bar using `bg-primary`)
- Option buttons: pill-style `<Button variant="outline">` — `border-border`, hover `border-primary` + `bg-primary/10`
- Step header: question text in `text-foreground`, step counter in `text-muted-foreground`
- Results panel: recommendation cards using `.glass-card`, match score badge in `bg-primary text-primary-foreground`
- Chat panel: AI explanation area with `bg-muted` background, scrollable, `text-muted-foreground` for AI text
- CTA: "Ver Recomendações" `<Button>` with `bg-primary text-primary-foreground` full-width on mobile

**Responsive behavior:**
- Mobile: full-screen wizard steps stacked vertically, options as pill buttons wrapping to 2 columns
- Tablet: centered card layout (max-w-lg), options in 2 columns
- Desktop: split layout — wizard left (40%), results/chat right (60%)

### Statistics (/statistics)

**Key design elements:**
- Page header: `<h1>` with `text-foreground`, subtitle in `text-muted-foreground`
- Tab bar: `<Tabs>` (Radix) with tabs: Overview, Rankings, Brands — active tab `border-b-2 border-primary`
- Scatter chart: dark background `bg-muted`, axis labels in `text-muted-foreground`, data points in `bg-primary`
- Data cards: metrics displayed in `.glass-card` with large number in `text-primary`, label in `text-muted-foreground`
- Rankings table: `bg-muted` rows, `border-border` dividers, rank badge in `bg-primary/20 text-primary`
- Brand section: brand logo cards in `.glass-card`, paddle count `<Badge>` in `bg-muted`
- Stat badges: `<Badge>` components throughout — `bg-primary/10 text-primary` for highlight stats

**Responsive behavior:**
- Mobile: tabs scroll horizontally, cards in single column, chart takes full width
- Tablet: 2-column card grid, full-width chart
- Desktop: 3-column card grid, chart beside top-level stats

---

## Component Mapping

| Stitch Element            | Project Component             | Import Path                    | Notes                          |
|---------------------------|-------------------------------|--------------------------------|--------------------------------|
| `<button>` pill           | `<Button variant="outline">`  | `@/components/ui/button`       | Add `rounded-full` for pill    |
| `<button>` primary CTA    | `<Button>`                    | `@/components/ui/button`       | Default variant = `bg-primary` |
| `<input>` text            | `<Input>`                     | `@/components/ui/input`        | Uses `bg-input border-input`   |
| Card with blur            | `<Card className="glass-card">`| `@/components/ui/card`        | `.glass-card` from globals.css |
| Subtle panel              | `<div className="glass">`     | N/A (utility class)            | `.glass` from globals.css      |
| Tab group                 | `<Tabs>` (Radix)              | `@/components/ui/tabs`         | Active = `border-b border-primary` |
| `<badge>` accent          | `<Badge>`                     | `@/components/ui/badge`        | `bg-primary/10 text-primary`   |
| `<badge>` neutral         | `<Badge variant="secondary">` | `@/components/ui/badge`        | `bg-muted text-muted-foreground` |
| Progress bar/dots         | Custom `<div>` progress       | N/A                            | `bg-primary` fill, `bg-muted` track |
| Scatter chart             | Chart.js or Recharts          | `recharts` (if available)      | Dark theme overrides needed    |
| Bottom navigation         | `<nav>` (bottom fixed)        | `@/components/ui/bottom-nav`   | `pb-safe` for iOS              |
| Glow accent text          | `<span className="text-glow">`| N/A (utility class)            | `.text-glow` from globals.css  |

---

## Design Patterns

### Glassmorphism Card Pattern
```tsx
<div className="glass-card rounded-xl p-4">
  {/* Content */}
</div>
```

### Lime Accent Heading Pattern
```tsx
<h1 className="text-foreground">
  Find your <span className="text-primary text-glow">perfect</span> paddle
</h1>
```

### Pill Option Button Pattern
```tsx
<Button
  variant={selected ? "default" : "outline"}
  className={cn(
    "rounded-full px-6",
    selected && "bg-primary text-primary-foreground",
    !selected && "border-border hover:border-primary hover:bg-primary/10"
  )}
>
  Option Label
</Button>
```

### Glow Hover Card Pattern
```tsx
<div className="glass-card rounded-xl glow-hover cursor-pointer">
  {/* Paddle card content */}
</div>
```

---

## Color Palette Summary

| Purpose               | Token Class            | Hex Value   |
|-----------------------|------------------------|-------------|
| Page background       | `bg-background`        | `#000000`   |
| Card/panel background | `bg-muted`             | `#111111`   |
| Borders               | `border-border`        | `#222222`   |
| Primary accent        | `text-primary` / `bg-primary` | `#ceff00` |
| Primary on lime bg    | `text-primary-foreground` | `#000000` |
| Body text             | `text-foreground`      | `#ffffff`   |
| Secondary text        | `text-muted-foreground` | `#a1a1aa`  |
| Glow shadow           | `shadow-glow`          | `rgba(206,255,0,0.3)` |

---

*Generated: 2026-03-23 | Plan: 17-01 | Source: tailwind.config.js + globals.css + component inventory*
*Update this file when Stitch MCP is available to add extracted screenshot data and HTML per screen.*
