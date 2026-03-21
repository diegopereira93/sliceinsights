import { Suspense } from 'react';
import { getApiBaseUrl } from '@/lib/api';
import CatalogClient from './catalog-client';
import { SkeletonGrid } from '@/components/catalog/catalog-grid';
import { CatalogResponse, CatalogStore } from '@/types/catalog';

export const revalidate = 3600;

function buildQueryString(searchParams: Record<string, string | string[] | undefined>): string {
  const params = new URLSearchParams();
  const mapping: Record<string, string> = {
    core_thickness: 'core_thickness',
    surface_material: 'surface_material',
    price_min: 'price_min',
    price_max: 'price_max',
    brand: 'brand',
    store: 'store',
    page: 'page',
  };

  for (const [key, apiKey] of Object.entries(mapping)) {
    const val = searchParams[key];
    if (val && typeof val === 'string') params.set(apiKey, val);
  }

  const page = searchParams.page ? Number(searchParams.page) : 1;
  params.set('limit', '24');
  const offset = (page - 1) * 24;
  if (offset > 0) params.set('offset', String(offset));

  return params.toString();
}

export default async function CatalogPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const apiBase = getApiBaseUrl();
  const qs = buildQueryString(searchParams);
  let initialData: CatalogResponse = { data: [], total: 0, limit: 24, offset: 0 };
  let initialStores: CatalogStore[] = [];

  try {
    const [paddlesRes, storesRes] = await Promise.all([
      fetch(`${apiBase}/catalog/paddles?${qs}`, { cache: 'no-store' }),
      fetch(`${apiBase}/catalog/stores`, { cache: 'no-store' }),
    ]);
    if (paddlesRes.ok) initialData = await paddlesRes.json();
    const storesJson = storesRes.ok ? await storesRes.json() : { data: [] };
    initialStores = storesJson.data ?? [];
  } catch {
    // CatalogClient handles empty state gracefully
  }

  return (
    <Suspense fallback={<SkeletonGrid />}>
      <CatalogClient initialData={initialData} initialStores={initialStores} />
    </Suspense>
  );
}
