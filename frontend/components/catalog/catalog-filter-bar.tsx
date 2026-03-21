'use client';

import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { CatalogFilters } from '@/types/catalog';
import { cn } from '@/lib/utils';

interface CatalogFilterBarProps {
  filters: CatalogFilters;
  onRemoveFilter: (key: keyof CatalogFilters) => void;
  total: number;
  children: React.ReactNode;
}

function ActiveFilterChips({
  filters,
  onRemove,
}: {
  filters: CatalogFilters;
  onRemove: (key: keyof CatalogFilters) => void;
}) {
  const chips: { label: string; key: keyof CatalogFilters; clear?: (keyof CatalogFilters)[] }[] = [];

  if (filters.brand) {
    chips.push({ label: filters.brand, key: 'brand' });
  }
  if (filters.core_thickness) {
    chips.push({ label: `${filters.core_thickness}mm`, key: 'core_thickness' });
  }
  if (filters.surface_material) {
    chips.push({ label: filters.surface_material, key: 'surface_material' });
  }
  if (filters.store) {
    chips.push({ label: filters.store, key: 'store' });
  }
  if (filters.price_min !== undefined || filters.price_max !== undefined) {
    const min = filters.price_min ?? 0;
    const max = filters.price_max ?? 4000;
    chips.push({
      label: `R$ ${min}-${max >= 4000 ? '4000+' : max}`,
      key: 'price_min',
      clear: ['price_min', 'price_max'],
    });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex gap-2 flex-wrap">
      {chips.map((chip) => (
        <Badge
          key={chip.key}
          className="bg-primary text-primary-foreground gap-1 text-xs font-bold"
        >
          {chip.label}
          <button
            aria-label={`Remover filtro ${chip.label}`}
            onClick={() => {
              onRemove(chip.key);
              if (chip.clear) {
                chip.clear.forEach((k) => {
                  if (k !== chip.key) onRemove(k);
                });
              }
            }}
            className="ml-1 hover:opacity-70 transition-opacity"
          >
            <X className="w-3 h-3" />
          </button>
        </Badge>
      ))}
    </div>
  );
}

export function CatalogFilterBar({
  filters,
  onRemoveFilter,
  total,
  children,
}: CatalogFilterBarProps) {
  return (
    <div className="sticky top-0 z-30 bg-background/80 backdrop-blur-md py-3 -mx-4 px-4 border-b border-border">
      <div className="flex items-center gap-3 flex-wrap">
        {children}
        <ActiveFilterChips filters={filters} onRemove={onRemoveFilter} />
      </div>
    </div>
  );
}
