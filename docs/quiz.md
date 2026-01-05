# Quiz: Pickleball Paddle Recommendation

**Plataforma:** Niterói Raquetes  
**Tipo:** Quiz de recomendação de produto (paddles de Pickleball)

---

## Quiz Otimizado (6 Perguntas)

A versão atual implementa 6 perguntas estratégicas, todas com impacto direto no algoritmo de recomendação.

### Pergunta 1: Foco Principal
> Com o que você precisa de mais ajuda no seu jogo?

| Opção | Valor | Mapeia para |
|-------|-------|-------------|
| ⚡ Gerar ataque | `offense` | `play_style: POWER` |
| 🎯 Jogo suave (dinks) | `soft_game` | `play_style: CONTROL` |
| ⚖️ Tudo um pouco | `everything` | `play_style: BALANCED` |

---

### Pergunta 2: Spin
> Quanto você valoriza o spin (efeito) na bola?

| Opção | Valor | Filtro Backend |
|-------|-------|----------------|
| 🔄 Muito importante | `high` | `spin_rating >= 8` |
| 🔄 Razoavelmente | `medium` | `spin_rating >= 5` |
| Não me importo | `low` | Sem filtro |

---

### Pergunta 3: Peso
> Qual sua preferência de peso da raquete?

| Opção | Valor | Filtro Backend |
|-------|-------|----------------|
| ⚖️ Mais pesada | `heavy` | `weight_avg_g >= 230` |
| ⚖️ Peso padrão | `standard` | `weight_avg_g 210-230` |
| ⚖️ Mais leve | `light` | `weight_avg_g <= 210` |
| Sem preferência | `no_preference` | Sem filtro |

---

### Pergunta 4: Nível
> Qual seu nível de habilidade no Pickleball?

| Opção | Valor Backend |
|-------|---------------|
| 🌱 Iniciante (3.0 ou menos) | `BEGINNER` |
| 🏃 Intermediário (3.5 - 4.0) | `INTERMEDIATE` |
| 🏆 Avançado (4.5+) | `ADVANCED` |

---

### Pergunta 5: Conforto
> Você tem alguma lesão ou sensibilidade (Tennis Elbow)?

| Opção | Valor Backend |
|-------|---------------|
| ❤️ Sim, busco conforto | `has_tennis_elbow: true` |
| ⚡ Não, sem restrições | `has_tennis_elbow: false` |

---

### Pergunta 6: Orçamento
> Qual seu orçamento máximo para a raquete?

| Opção | Valor (BRL) |
|-------|-------------|
| 💰 Até R$ 800 | `800` |
| 💰 Até R$ 1.500 | `1500` |
| 💰 Até R$ 2.500 | `2500` |
| 🏆 Sem limite | `10000` |

---

## Mapeamento para API

Todas as 6 respostas são utilizadas pelo backend:

```typescript
function mapAnswersToRequest(answers): RecommendationRequest {
    return {
        skill_level: answers.skill_level,      // Q4
        play_style: derivadoDeQ1,              // Q1
        has_tennis_elbow: answers.has_tennis_elbow === 'true',  // Q5
        budget_max_brl: parseFloat(answers.budget),             // Q6
        spin_preference: answers.spin_value,    // Q2 (NEW)
        weight_preference: answers.weight_preference,  // Q3 (NEW)
        limit: 1
    };
}
```

### Request Final

```json
POST /api/v1/recommendations
{
  "skill_level": "INTERMEDIATE",
  "play_style": "CONTROL",
  "has_tennis_elbow": false,
  "budget_max_brl": 1500,
  "spin_preference": "high",
  "weight_preference": "light",
  "limit": 1
}
```

---

## Histórico

### v2.0 (Atual) - 6 Perguntas Otimizadas

Perguntas removidas por baixo impacto:
- ~~Q2 Prioridade~~ → Redundante com Q1
- ~~Q3 Erros~~ → Baixo poder preditivo
- ~~Q4 Empunhadura~~ → Irrelevante para pickleball
- ~~Q9 Singles/Doubles~~ → Derivável de outras respostas

### v1.0 - 10 Perguntas

Versão original adaptada do RevenueHunt template.
