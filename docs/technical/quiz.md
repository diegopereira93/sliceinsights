# Quiz: Pickleball Paddle Recommendation

**Plataforma:** SliceInsights / Niterói Raquetes  
**Tipo:** Quiz de recomendação de produto (paddles de Pickleball)  
**Versão:** 3.0 (10 Perguntas)

---

## Quiz Atual (10 Perguntas)

A versão v1.6 implementa 10 perguntas estratégicas, cobrindo nível de habilidade, estilo de jogo, preferências de spin, peso, e orçamento.

### Mapeamento das Perguntas

| # | Pergunta | Chave (`key`) | Impacto no Algoritmo |
|---|----------|---------------|----------------------|
| 1 | Nível de habilidade | `skill_level` | Filtra raquetes por complexidade |
| 2 | Esportes anteriores | `previous_sports` | UX (engajamento) |
| 3 | Formato de jogo (Singles/Duplas) | `format_preference` | Influencia `play_style` se BALANCED |
| 4 | Área de ajuda (Offense/Defense/Soft Game) | `help_with` | Deriva `play_style` (POWER/CONTROL/BALANCED) |
| 5 | Slider Power/Control | `play_style_mix` | `power_preference_percent` (0-100%) |
| 6 | Importância do Spin | `spin_value` | Filtro `spin_preference` (high/medium) |
| 7 | Preferência de Peso | `weight_preference` | Filtro `weight_preference` (light/standard/heavy) |
| 8 | Comprimento do Cabo | `handle_preference` | UX (engajamento) |
| 9 | Frequência de Jogo | `play_frequency` | UX (engajamento) |
| 10 | Lesões (Tennis Elbow) | `has_tennis_elbow` | Filtro `core_thickness_mm >= 16` |
| 11 | Orçamento | `budget` | Filtro `budget_max_brl` |

---

## Request Final

```json
POST /api/v1/recommendations
{
  "skill_level": "intermediate",
  "play_style": "balanced",
  "has_tennis_elbow": false,
  "budget_max_brl": 1600,
  "spin_preference": "high",
  "weight_preference": "light",
  "power_preference_percent": 50,
  "limit": 1
}
```

---

## Funções de Mapeamento (Frontend)

```typescript
// frontend/components/paddle/racket-finder-quiz.tsx

function mapAnswersToRequest(answers: Record<string, string>): RecommendationRequest {
    // Deriva play_style de help_with (Q4)
    let play_style: 'power' | 'control' | 'balanced' = 'balanced';
    if (answers.help_with === 'offense') play_style = 'power';
    else if (answers.help_with === 'soft_game' || answers.help_with === 'defense') play_style = 'control';

    // Ajusta se format_preference for 'singles' e play_style ainda for 'balanced'
    if (play_style === 'balanced' && answers.format_preference === 'singles') {
        play_style = 'power';
    }

    const powerMix = answers.play_style_mix ? parseInt(answers.play_style_mix) : undefined;

    return {
        skill_level: answers.skill_level || 'intermediate',
        play_style: powerMix !== undefined ? 'balanced' : play_style,
        has_tennis_elbow: answers.has_tennis_elbow === 'true',
        budget_max_brl: parseFloat(answers.budget) || 3000,
        spin_preference: (answers.spin_value === 'high' || answers.spin_value === 'medium') ? answers.spin_value : undefined,
        weight_preference: (answers.weight_preference === 'light' || answers.weight_preference === 'heavy') ? answers.weight_preference : undefined,
        power_preference_percent: powerMix,
        limit: 1
    };
}
```

---

## Histórico

### v3.0 (Atual) - 10 Perguntas + Slider
Reimplementação com foco em engajamento ("Labor Illusion") e slider de Power/Control para preferência precisa.

### v2.0 - 6 Perguntas Otimizadas
Versão enxuta, removendo perguntas de baixo impacto.

### v1.0 - 10 Perguntas (Template RevenueHunt)
Versão original adaptada.
