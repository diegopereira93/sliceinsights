// Production Render backend URL - hardcoded fallback for SSR on Vercel
// (vercel.json env vars are not available at runtime for SSR)
const RENDER_BACKEND_URL = 'https://sliceinsights.onrender.com/api/v1';

// Get API base URL at runtime - called for each request, not at module load time
// This is critical for proper SSR behavior on Vercel where env vars behave differently
export const getApiBaseUrl = (): string => {
    const isBrowser = typeof window !== 'undefined';

    // SERVER-SIDE (Docker/Local): Use internal network to avoid ECONNREFUSED
    if (!isBrowser && process.env.BACKEND_URL) {
        // BACKEND_URL is typically "http://backend:8000" or "https://url.com"
        // We ensure we don't double apppend /api/v1 if it's already there (though usually it's not)
        return process.env.BACKEND_URL.includes('/api/v1')
            ? process.env.BACKEND_URL
            : `${process.env.BACKEND_URL}/api/v1`;
    }

    // CLIENT-SIDE or Vercel Fallback: Use configured public URL
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL;
    }

    // Browser Fallback: use relative path (rewrites will handle it)
    if (isBrowser) {
        return `${window.location.origin}/api/v1`;
    }

    // Ultimate Fallback
    return RENDER_BACKEND_URL;
};

// Alias for backwards compatibility
export const API_BASE_URL = RENDER_BACKEND_URL;

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

    const url = `${getApiBaseUrl()}/paddles?${params.toString()}`;
    console.log('[SSR] Fetching paddles from:', url);

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout for cold starts

        const response = await fetch(url, {
            signal: controller.signal,
            cache: 'no-store', // Ensure fresh data
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            console.error('[SSR] Paddles fetch failed with status:', response.status);
            throw new Error('Failed to fetch paddles');
        }
        const data = await response.json();
        console.log('[SSR] Paddles fetched successfully, count:', data.data?.length || 0);
        return data;
    } catch (error) {
        console.error('[SSR] Paddles fetch error:', error);
        throw error;
    }
}

export async function getBrands(filters: { available_in_brazil?: boolean } = {}) {
    const params = new URLSearchParams();
    if (filters.available_in_brazil !== undefined) {
        params.append('available_in_brazil', filters.available_in_brazil.toString());
    }

    const url = `${getApiBaseUrl()}/brands?${params.toString()}`;
    console.log('[SSR] Fetching brands from:', url);

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

        const response = await fetch(url, {
            signal: controller.signal,
            cache: 'no-store',
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            console.error('[SSR] Brands fetch failed with status:', response.status);
            throw new Error('Failed to fetch brands');
        }
        const data = await response.json();
        console.log('[SSR] Brands fetched successfully, count:', data.data?.length || 0);
        return data;
    } catch (error) {
        console.error('[SSR] Brands fetch error:', error);
        throw error;
    }
}

export async function getRecommendations(request: RecommendationRequest) {
    const response = await fetch(`${getApiBaseUrl()}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to fetch recommendations');
    return response.json();
}

export async function searchPaddles(query: string) {
    const response = await fetch(`${getApiBaseUrl()}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search paddles');
    return response.json();
}

export async function getPaddleById(id: string) {
    const response = await fetch(`${getApiBaseUrl()}/paddles/${id}`);
    if (!response.ok) throw new Error('Failed to fetch paddle details');
    return response.json();
}

export async function getPaddlePriceHistory(id: string, days: number = 30) {
    const response = await fetch(`${getApiBaseUrl()}/paddles/${id}/history?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch paddle history');
    return response.json();
}

import { Paddle } from '@/components/paddle/paddle-card';

export function mapBackendToFrontendPaddle(bp: BackendPaddle): Paddle {
    // Helper: Generate deterministic pseudo-random number from string
    const stringHash = (str: string) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash);
    };

    const hash = stringHash(bp.model_name + bp.brand_name);
    const pseudoRandom = (min: number, max: number, offset: number) => {
        return min + ((hash + offset) % (100 * (max - min))) / 100;
    };

    // Check if we have real data (Swing Weight is a good proxy for data quality)
    const hasRealSpecs = bp.specs.swing_weight != null && bp.specs.swing_weight > 0;
    const hasRealRatings = bp.ratings.power !== 5 || bp.ratings.control !== 5; // Assuming 5 is the default fallback

    let power, control, spin, sweetSpot, swingWeight, twistWeight;

    if (hasRealSpecs || hasRealRatings) {
        // Use Real Data
        power = bp.ratings.power ?? bp.specs.power_original ?? 5;
        twistWeight = bp.specs.twist_weight || 0;

        control = bp.ratings.control;
        if (control === undefined || control === 0) {
            if (twistWeight > 100) {
                control = Number(((twistWeight - 150) / (600 - 150) * 10).toFixed(1));
                control = Math.min(Math.max(control, 0), 10);
            } else {
                control = Math.min(Number((twistWeight * 1.5).toFixed(1)), 10);
            }
        }

        spin = bp.ratings.spin;
        if (spin === undefined || spin === 0) {
            const rpm = bp.specs.spin_rpm ?? 0;
            spin = rpm >= 150 ? Math.min(Number(((rpm - 150) / (300 - 150) * 10).toFixed(1)), 10) : (rpm === 0 ? 5 : 0);
        }

        sweetSpot = bp.ratings.sweet_spot;
        if (sweetSpot === undefined || sweetSpot === 0) {
            sweetSpot = Math.max(1, Number((10 - (control || 5) * 0.4).toFixed(1)));
        }

        swingWeight = bp.specs.swing_weight;
    } else {
        // Generate Synthetic Data for UI Validation
        power = Number(pseudoRandom(6, 9.5, 1).toFixed(1));
        control = Number(pseudoRandom(6, 9.5, 2).toFixed(1));
        spin = Number(pseudoRandom(5, 10, 3).toFixed(1));
        sweetSpot = Number(pseudoRandom(6, 9, 4).toFixed(1));
        swingWeight = Math.floor(pseudoRandom(105, 125, 5));
        twistWeight = Number(pseudoRandom(5.5, 7.5, 6).toFixed(2));
    }

    return {
        id: bp.id,
        name: bp.model_name,
        brand: bp.brand_name || 'Brand',
        price: bp.min_price_brl || 0,
        image: bp.image_url || `https://placehold.co/400x533/png?text=${encodeURIComponent(bp.model_name)}`,
        rating: Number(((power + control + spin) / 3).toFixed(1)),
        weight: 'N/A',
        surfaceMaterial: bp.specs.face_material || (hash % 2 === 0 ? 'Carbon Fiber' : 'Fiberglass'),
        faceMaterial: bp.specs.face_material,
        coreMaterial: bp.specs.core_material,
        gripCircumference: bp.specs.grip_circumference,
        powerLevel: power >= 8 ? 'High' : power >= 6.5 ? 'Medium' : 'Low',
        controlLevel: control >= 8 ? 'High' : control >= 6.5 ? 'Medium' : 'Low',
        power: power,
        control: control,
        spin: spin,
        sweetSpot: sweetSpot,
        tags: bp.is_featured ? ['Destaque'] : [],
        matchReasons: [],
        availableInBrazil: bp.available_in_brazil,
        swingWeight: swingWeight,
        twistWeight: bp.specs.twist_weight || twistWeight, // Use real if available
        spinRPM: bp.specs.spin_rpm || Math.floor(spin * 200),
        powerOriginal: bp.specs.power_original,
        coreThicknessmm: bp.specs.core_thickness_mm || (hash % 3 === 0 ? 14 : 16),
        handleLength: bp.specs.handle_length,
        isSynthetic: !hasRealSpecs && !hasRealRatings,
        dataQuality: (hasRealSpecs || hasRealRatings) ? 'Verified' : 'Estimated'
    };
}

export interface AlertResponse {
    id: number;
    message: string;
}

export async function subscribeToAlert(paddleId: string, email: string, targetPrice_brl: number): Promise<AlertResponse> {
    const res = await fetch(`${getApiBaseUrl()}/alerts`, {
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
// Build timestamp: 20260127201245
