export interface CatalogOffer {
  store_name: string;
  price_brl: number;
  store_url: string;
}

export interface CatalogPaddle {
  id: string;
  brand: string | null;
  model_name: string;
  image_url: string | null;
  specs: {
    core_thickness_mm: number | null;
    surface_material: string | null;
  };
  market_offers: CatalogOffer[];
}

export interface CatalogStore {
  id: number;
  name: string;
  slug: string;
  base_url: string;
  is_active: boolean;
  available_brands: string[];
}

export interface CatalogFilters {
  core_thickness?: string;
  surface_material?: string;
  price_min?: number;
  price_max?: number;
  brand?: string;
  store?: string;
  page: number;
}

export interface CatalogResponse {
  data: CatalogPaddle[];
  total: number;
  limit: number;
  offset: number;
}

export interface CatalogStoresResponse {
  data: CatalogStore[];
  total: number;
}
