# API Specification - PickleMatch Advisor

## Base URL

```
Development: http://localhost:8002/api/v1
Production:  https://api.picklematch.com/v1
```

---

## Authentication

MVP: **Sem autenticação** (público)

Futuro: API Key ou JWT para partners

---

## Endpoints

### Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

**Response (503 Service Unavailable):**
```json
{
  "detail": "Database unavailable"
}
```

> **Note:** O health check valida a conexão com o banco de dados.

---

### Brands

#### List All Brands

```http
GET /brands
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Drop Shot",
      "website": "https://dropshot.es"
    },
    {
      "id": 2,
      "name": "Joola",
      "website": "https://joola.com"
    }
  ],
  "total": 5
}
```

---

### Paddles

#### List All Paddles

```http
GET /paddles
```

**Query Parameters:**

| Param           | Type    | Description                        |
| --------------- | ------- | ---------------------------------- |
| `brand_id`      | int     | Filtrar por marca                  |
| `skill_level`   | string  | `beginner`, `intermediate`, `advanced` |
| `min_price`     | decimal | Preço mínimo (BRL)                 |
| `max_price`     | decimal | Preço máximo (BRL)                 |
| `limit`         | int     | Número de resultados (default: 20) |
| `offset`        | int     | Paginação                          |

**Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "brand": {
        "id": 1,
        "name": "Drop Shot"
      },
      "model_name": "Conqueror 13mm",
      "specs": {
        "core_thickness_mm": 13.0,
        "weight_avg_g": 230,
        "face_material": "carbon",
        "shape": "elongated"
      },
      "ratings": {
        "power": 9,
        "control": 6,
        "spin": 8,
        "sweet_spot": 7
      },
      "ideal_for_tennis_elbow": false,
      "skill_level": "advanced",
      "min_price_brl": 899.90,
      "offers_count": 3
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

#### Get Paddle Details

```http
GET /paddles/{paddle_id}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "brand": {
    "id": 1,
    "name": "Drop Shot",
    "website": "https://dropshot.es"
  },
  "model_name": "Conqueror 13mm",
  "search_keywords": ["conqueror", "dropshot", "13mm", "power"],
  "specs": {
    "core_thickness_mm": 13.0,
    "weight_avg_g": 230,
    "face_material": "carbon",
    "shape": "elongated"
  },
  "ratings": {
    "power": 9,
    "control": 6,
    "spin": 8,
    "sweet_spot": 7
  },
  "ideal_for_tennis_elbow": false,
  "skill_level": "advanced",
  "market_offers": [
    {
      "store_name": "Amazon",
      "price_brl": 899.90,
      "url": "https://amazon.com.br/...",
      "last_updated": "2024-01-15T10:30:00Z"
    },
    {
      "store_name": "YoSports",
      "price_brl": 949.00,
      "url": "https://yosports.com.br/...",
      "last_updated": "2024-01-14T15:00:00Z"
    }
  ]
}
```

---

### Recommendations (Core Endpoint)

**Response:**
```json
{
  "user_profile": {
    "skill_level": "intermediate",
    "budget_max_brl": 1200.00,
    "play_style": "control",
    "has_tennis_elbow": false
  },
  "recommendations": [
    {
      "rank": 1,
      "paddle_id": "...",
      "brand_name": "Joola",
      "model_name": "Perseus 16mm",
      "ratings": {
        "power": 7,
        "control": 9,
        "spin": 8,
        "sweet_spot": 8
      },
      "min_price_brl": 1099.00,
      "match_reasons": [
        "Alto control rating (9/10)",
        "Ideal para estilo Control"
      ],
      "tags": ["Top Pick", "Melhor Controle"]
    }
  ],
  "filters_applied": {
    "budget_filter": true,
    "tennis_elbow_filter": false
  },
  "total_matching": 8,
  "returned": 1
}
```

**Error Responses:**

```json
// 400 Bad Request
{
  "detail": [
    {
      "loc": ["body", "skill_level"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

// 422 Unprocessable Entity
{
  "detail": "Invalid play_style. Must be one of: power, control, balanced"
}
```

---

### Search

#### Fuzzy Search Paddles

```http
GET /search?q={query}
```

**Query Parameters:**

| Param | Type   | Description                    |
| ----- | ------ | ------------------------------ |
| `q`   | string | Search query (min 2 chars)     |
| `limit` | int  | Max results (default: 10)      |

**Example:**
```http
GET /search?q=conqu&limit=5
```

**Response:**
```json
{
  "query": "conqu",
  "results": [
    {
      "id": "...",
      "brand_name": "Drop Shot",
      "model_name": "Conqueror 13mm",
      "match_score": 95,
      "min_price_brl": 899.90
    }
  ],
  "total": 1
}
```

---

## Error Codes

| Code | Description                                      |
| ---- | ------------------------------------------------ |
| 400  | Bad Request - Invalid parameters                 |
| 404  | Not Found - Resource doesn't exist               |
| 422  | Unprocessable Entity - Validation failed         |
| 500  | Internal Server Error                            |

---

## Rate Limiting

**Implementado via SlowAPI**

| Endpoint | Limite |
|----------|--------|
| `/recommendations` | 30 req/min |
| `/search` | 60 req/min |
| `/paddles` | 100 req/min |

**Response (429 Too Many Requests):**
```json
{
  "error": "Rate limit exceeded",
  "detail": "30 per 1 minute"
}
```

---

## Metrics (Prometheus)

```http
GET /metrics
```

Retorna métricas no formato Prometheus para monitoramento:
- Request latency
- Request count by endpoint
- Error rates

---

## OpenAPI/Swagger

Documentação automática disponível em:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
