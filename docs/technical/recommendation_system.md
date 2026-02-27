# Recommendation System Logic

This document details the technical implementation of the SliceInsights recommendation engine, including rating synthesis, ranking formulas, and value score calculation.

## 1. Unified Rating Synthesis

To ensure consistency between the recommendation engine and the user interface, all paddle ratings are synthesized from raw physical specifications using a centralized function `calculate_paddle_ratings`.

All ratings are normalized to a **0.0 - 10.0 scale**.

### Control (Stability)
The control rating is derived from `twist_weight`. The system handles two different data scales:
- **Large Scale (Degrees)**: If `twist_weight > 100` (typically 150-600).
  - Formula: `(twist_weight - 150) / 450 * 10`
- **Small Scale (Proxy)**: If `twist_weight <= 100` (typically 5.0-7.5).
  - Formula: `twist_weight * 1.5`
- **Constraints**: Minimum 0.0, Maximum 10.0.

### Spin
The spin rating is derived from `spin_rpm`.
- **Primary Range**: 150 - 300 (standardized from raw RPM values in current dump).
- **Formula**: `(spin_rpm - 150) / 150 * 10`
- **Missing Data**: Defaults to 5.0 if `spin_rpm == 0`.

### Power
The power rating is currently based on a pre-calculated `power_rating` field in the database (0-10).
- **Default**: 5.0 if missing.

### Sweet Spot (Forgiveness)
The sweet spot is synthesized inversely from the stability/control rating to represent technical trade-offs.
- **Formula**: `max(1.0, 10.0 - (control * 0.4))`

---

## 2. Ranking Strategy

The recommendation engine uses a multi-stage approach to find the best paddles for a user profile.

### Hard Filters (SQL Level)
1. **Tennis Elbow**: If `has_tennis_elbow` is true, only paddles with `core_thickness_mm >= 16.0` are selected.
2. **Budget**: Only paddles with a minimum market price ≤ `budget_max_brl` are selected.
3. **Weight Preference**:
   - `light`: `swing_weight <= 110`
   - `standard`: `swing_weight` between 110 and 120
   - `heavy`: `swing_weight >= 120`

### Smart AI Ranking (v1.8 - Hybrid)
Após a filtragem SQL, as raquetes são processadas pelo **Serviço de IA (Llama 3.3)**:

1. **Seleção de Candidatos**: O motor seleciona os 20 melhores candidatos via SQL (based on budget and availability).
2. **Refinamento Qualitativo**: A IA analisa termos como "Pro", "Performance" e "Control" no nome do modelo e marca para garantir que o nível de habilidade (Beginner/Advanced) seja rigorosamente respeitado.
3. **Diversity Jitter**: Aplicação de um jitter de ranqueamento para garantir que marcas diversas (Engage, Proxr, Selkirk) apareçam nos resultados, evitando o monopólio de uma única marca.
4. **Dossiê do Coach**: Geração de uma análise técnica personalizada (`grok_dossier`) que explica a escolha baseada nos specs reais e no perfil do usuário.

---

## 3. Trava Médica (Tennis Elbow)

O sistema implementa uma camada de segurança dupla:
- **Camada 1 (SQL)**: Bloqueio rígido de raquetes com `core_thickness_mm < 16.0`.
- **Camada 2 (IA)**: O prompt da IA é instruído a priorizar tecnologias de conforto e "Touch" para usuários com restrições físicas.

---

## 4. Value Score Calculation

O `value_score` ajuda usuários a identificar "best deals" comparando a performance técnica agregada ao preço de mercado em BRL.

- **Fórmula**: `(Performance Agregada / Preço) * 1000`
- **Uso**: Serve como critério de desempate no pool de candidatos antes do ranking final de IA.

---

## 5. Dossiê e Insights

Diferente do v1.7 (tags estáticas), o v1.8 gera um **Dossiê Técnico** dinâmico:
- **Tom**: Treinador Profissional.
- **Adaptação**: O vocabulário muda conforme o nível do aluno (explicativo para iniciantes, técnico para avançados).
- **Objetividade**: Cita specs reais (RPM, Swing Weight) se a confiança dos dados (`specs_confidence`) for alta.
