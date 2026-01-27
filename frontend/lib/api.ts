const isBrowser = typeof window !== 'undefined';

// For SSR on Vercel, NEXT_PUBLIC_API_URL is available at runtime in the server environment
// BACKEND_URL is an internal URL for Docker-based development
const INTERNAL_API_URL = (process.env.BACKEND_URL || 'http://backend_v3:8000').replace(/\/$/, '') + '/api/v1';
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || (isBrowser ? `${window.location.origin}/api/v1` : INTERNAL_API_URL);

// Always prefer the public URL for both client and server when available
export const API_BASE_URL = PUBLIC_API_URL;

export interface BackendPaddle {
    id: string;
    brand_id: number;
    brand_name: string;
    model_name: string;
    image_url: string | null;
    is_featured: boolean;
    specs: {
        core_thickness_mm: number;
        core_material?: string;
        face_material?: string;
        swing_weight?: number;
        twist_weight?: number;
        spin_rpm?: number;
        power_original?: number;
        handle_length?: string;
        grip_circumference?: string;
    };
    ratings: {
        power: number;
        control: number;
        spin: number;
        sweet_spot: number;
    };
    available_in_brazil?: boolean;
    min_price_brl: number | null;
    offers_count: number;
}

export interface RecommendationRequest {
    skill_level: string;
    budget_max_brl?: number;
    play_style: string;
    has_tennis_elbow: boolean;
    spin_preference?: 'high' | 'medium' | 'low';
    weight_preference?: 'heavy' | 'standard' | 'light';
    power_preference_percent?: number;
    limit: number;
}

export interface Recommendation {
    rank: number;
    paddle_id: string;
    brand_name: string;
    model_name: string;
    ratings: Record<string, number>;
    min_price_brl: number | null;
    match_reasons: string[];
    tags: string[];
    value_score?: number;
}

export async function getPaddles(filters: Record<string, any> = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            params.append(key, value.toString());
        }
    });

    const response = await fetch(`${API_BASE_URL}/paddles?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch paddles');
    return response.json();
}

export async function getBrands() {
    const response = await fetch(`${API_BASE_URL}/brands`);
    if (!response.ok) throw new Error('Failed to fetch brands');
    return response.json();
}

export async function getRecommendations(request: RecommendationRequest) {
    const response = await fetch(`${API_BASE_URL}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to fetch recommendations');
    return response.json();
}

export async function searchPaddles(query: string) {
    const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search paddles');
    return response.json();
}

export async function getPaddleById(id: string) {
    const response = await fetch(`${API_BASE_URL}/paddles/${id}`);
    if (!response.ok) throw new Error('Failed to fetch paddle details');
    return response.json();
}

import { Paddle } from '@/components/paddle/paddle-card';

export function mapBackendToFrontendPaddle(bp: BackendPaddle): Paddle {
    // 1. Get synthesized ratings from backend if available, otherwise compute them
    // (Backend uses twist_weight 150-600 for control/sweet spot)
    const power = bp.ratings.power ?? bp.specs.power_original ?? 5;

    // Fallback logic if backend ratings are missing or we need extra precision
    const twist = bp.specs.twist_weight || 0;
    let control = bp.ratings.control;
    if (control === undefined || control === 0) {
        if (twist > 100) {
            control = Number(((twist - 150) / (600 - 150) * 10).toFixed(1));
            control = Math.min(Math.max(control, 0), 10);
        } else {
            control = Math.min(Number((twist * 1.5).toFixed(1)), 10);
        }
    }

    let spin = bp.ratings.spin;
    if (spin === undefined || spin === 0) {
        const rpm = bp.specs.spin_rpm ?? 0;
        spin = rpm >= 150 ? Math.min(Number(((rpm - 150) / (300 - 150) * 10).toFixed(1)), 10) : (rpm === 0 ? 5 : 0);
    }

    let sweetSpot = bp.ratings.sweet_spot;
    if (sweetSpot === undefined || sweetSpot === 0) {
        sweetSpot = Math.max(1, Number((10 - control * 0.4).toFixed(1)));
    }

    return {
        id: bp.id,
        name: bp.model_name,
        brand: bp.brand_name || 'Brand',
        price: bp.min_price_brl || 0,
        image: bp.image_url || `https://placehold.co/400x533/png?text=${encodeURIComponent(bp.model_name)}`,
        rating: (power + control + spin) / 3, // Visual overall rating
        weight: 'N/A',
        surfaceMaterial: bp.specs.face_material || 'Carbon',
        faceMaterial: bp.specs.face_material,
        coreMaterial: bp.specs.core_material,
        gripCircumference: bp.specs.grip_circumference,
        powerLevel: power >= 8 ? 'High' : power >= 5 ? 'Medium' : 'Low',
        controlLevel: control >= 8 ? 'High' : control >= 5 ? 'Medium' : 'Low',
        power: power,
        control: control,
        spin: spin,
        sweetSpot: sweetSpot,
        tags: bp.is_featured ? ['Destaque'] : [],
        matchReasons: [],
        availableInBrazil: bp.available_in_brazil,
        swingWeight: bp.specs.swing_weight,
        twistWeight: bp.specs.twist_weight,
        spinRPM: bp.specs.spin_rpm,
        powerOriginal: bp.specs.power_original,
        coreThicknessmm: bp.specs.core_thickness_mm,
        handleLength: bp.specs.handle_length,
    };
}

export interface AlertResponse {
    id: number;
    message: string;
}

export async function subscribeToAlert(paddleId: string, email: string, targetPrice_brl: number): Promise<AlertResponse> {
    const res = await fetch(`${API_BASE_URL}/alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            paddle_id: paddleId,
            user_email: email,
            target_price: targetPrice_brl
        }),
    });

    if (!res.ok) throw new Error('Failed to create alert');
    return res.json();
}
