export interface MarketOffer {
  store_name: string;
  price_brl: number;
  store_url: string;
}

export interface PaddleRecommendation {
  rank: number;
  paddle_id: string;
  brand_name: string;
  model_name: string;
  image_url: string | null;
  ratings: Record<string, number | null>;
  min_price_brl: number | null;
  market_offers: MarketOffer[];
  match_reasons: string[];
  tags: string[];
  value_score: number | null;
}

export interface RecommendationResult {
  user_profile: Record<string, unknown>;
  recommendations: PaddleRecommendation[];
  filters_applied: Record<string, boolean>;
  total_matching: number;
  returned: number;
  grok_dossier: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
}

export interface RecommendationRequest {
  skill_level: 'beginner' | 'intermediate' | 'advanced' | null;
  play_style: 'power' | 'control' | 'balanced' | null;
  budget_max_brl: number | null;
  has_tennis_elbow: boolean;
  weight_preference: 'heavy' | 'standard' | 'light' | 'no_preference' | null;
  limit: number;
}