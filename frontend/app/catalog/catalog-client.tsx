'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api';
import { CatalogResponse, CatalogStore, CatalogFilters } from '@/types/catalog';
import { CatalogGrid } from '@/components/catalog/catalog-grid';
import { CatalogPagination } from '@/components/catalog/catalog-pagination';
import { CatalogFilterBar } from '@/components/catalog/catalog-filter-bar';
import { FilterDrawer } from '@/components/paddle/filter-drawer';

const PAGE_SIZE = 24;

interface CatalogClientProps {
  initialData: CatalogResponse;
  initialStores: CatalogStore[];
}

function readFiltersFromParams(params: URLSearchParams): CatalogFilters {
  return {
    core_thickness: params.get('core_thickness') ?? undefined,
    surface_material: params.get('surface_material') ?? undefined,
    price_min: params.get('price_min') ? Number(params.get('price_min')) : undefined,
    price_max: params.get('price_max') ? Number(params.get('price_max')) : undefined,
    brand: params.get('brand') ?? undefined,
    store: params.get('store') ?? undefined,
    page: params.get('page') ? Number(params.get('page')) : 1,
  };
}

function filtersToQueryString(filters: CatalogFilters): string {
  const params = new URLSearchParams();
  if (filters.core_thickness) params.set('core_thickness', filters.core_thickness);
  if (filters.surface_material) params.set('surface_material', filters.surface_material);
  if (filters.price_min && filters.price_min > 0) params.set('price_min', String(filters.price_min));
  if (filters.price_max && filters.price_max < 4000) params.set('price_max', String(filters.price_max));
  if (filters.brand) params.set('brand', filters.brand);
  if (filters.store) params.set('store', filters.store);
  if (filters.page > 1) params.set('page', String(filters.page));
  params.set('limit', String(PAGE_SIZE));
  const offset = (filters.page - 1) * PAGE_SIZE;
  if (offset > 0) params.set('offset', String(offset));
  return params.toString();
}

export default function CatalogClient({ initialData, initialStores }: CatalogClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState<CatalogResponse>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
  const [filters, setFilters] = useState<CatalogFilters>(() => readFiltersFromParams(searchParams));
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isFirstRender = useRef(true);

  // Debounced fetch effect — depends only on filters, not searchParams
  useEffect(() => {
    // Skip fetch on initial render — SSR data is already loaded
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      setIsError(false);
      const qs = filtersToQueryString(filters);
      router.replace(`/catalog?${qs}`, { scroll: false });
      try {
        const res = await fetch(`${getApiBaseUrl()}/catalog/paddles?${qs}`);
        if (!res.ok) throw new Error('fetch failed');
        setData(await res.json());
      } catch {
        setIsError(true);
      } finally {
        setIsLoading(false);
      }
    }, 400);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateFilter = (key: keyof CatalogFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const removeFilter = (key: keyof CatalogFilters) => {
    setFilters(prev => {
      const next = { ...prev, page: 1 };
      delete next[key];
      return next;
    });
  };

  const clearAllFilters = () => {
    setFilters({ page: 1 });
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalPages = Math.ceil(data.total / PAGE_SIZE);
  const activeFilterCount = [
    filters.brand, filters.core_thickness, filters.surface_material, filters.store,
    (filters.price_min && filters.price_min > 0) || (filters.price_max && filters.price_max < 4000) ? 'price' : undefined
  ].filter(Boolean).length;

  return (
    <main className="px-4 pt-6 pb-24">
      <h1 className="text-xl font-bold">Catalogo de Raquetes</h1>
      <p className="text-sm text-muted-foreground mb-4">
        {data.total} raquetes disponiveis no Brasil
      </p>

      <CatalogFilterBar
        filters={filters}
        onRemoveFilter={removeFilter}
        total={data.total}
      >
        <FilterDrawer
          brands={[...new Set(initialData.data.map(p => p.brand).filter(Boolean) as string[])]}
          selectedBrands={filters.brand ? [filters.brand] : []}
          onToggleBrand={(brand) => { filters.brand === brand ? removeFilter('brand') : updateFilter('brand', brand); }}
          priceRange={[filters.price_min ?? 0, filters.price_max ?? 4000]}
          onPriceRangeChange={([min, max]) => {
            setFilters(prev => ({ ...prev, price_min: min > 0 ? min : undefined, price_max: max < 4000 ? max : undefined, page: 1 }));
          }}
          thicknessFilter={filters.core_thickness ? `${filters.core_thickness}mm` as any : "all"}
          onThicknessChange={(v) => { v === "all" ? removeFilter('core_thickness') : updateFilter('core_thickness', v.replace('mm', '')); }}
          surfaceMaterialFilter={(filters.surface_material as any) ?? "all"}
          onSurfaceMaterialChange={(v) => { v === "all" ? removeFilter('surface_material') : updateFilter('surface_material', v); }}
          storeFilter={filters.store ?? "all"}
          onStoreChange={(slug) => { slug === "all" ? removeFilter('store') : updateFilter('store', slug); }}
          stores={initialStores.map(s => ({ name: s.name, slug: s.slug }))}
          onClear={clearAllFilters}
        />
      </CatalogFilterBar>

      <div className="mt-4">
        <CatalogGrid
          paddles={data.data}
          isLoading={isLoading}
          isError={isError}
          total={data.total}
          onClearFilters={clearAllFilters}
          onRetry={() => setFilters(prev => ({ ...prev }))}
        />
      </div>

      <CatalogPagination
        currentPage={filters.page}
        totalPages={totalPages}
        onPageChange={handlePageChange}
      />
    </main>
  );
}
