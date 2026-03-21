'use client';

import { CatalogPaddle } from '@/types/catalog';
import { CatalogPaddleCard } from './catalog-paddle-card';
import { EmptyState } from '@/components/ui/empty-state';

export function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="glass-card rounded-xl overflow-hidden">
          <div className="aspect-[4/5] bg-muted animate-pulse" />
          <div className="p-4 space-y-3">
            <div className="flex gap-2">
              <div className="h-5 w-16 bg-muted animate-pulse rounded-full" />
              <div className="h-5 w-12 bg-muted animate-pulse rounded-full" />
            </div>
            <div className="h-4 w-2/3 bg-muted animate-pulse rounded" />
            <div className="h-4 w-1/3 bg-muted animate-pulse rounded" />
            <div className="h-8 w-full bg-muted animate-pulse rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface CatalogGridProps {
  paddles: CatalogPaddle[];
  isLoading: boolean;
  isError: boolean;
  total: number;
  onClearFilters: () => void;
  onRetry: () => void;
}

export function CatalogGrid({
  paddles,
  isLoading,
  isError,
  total,
  onClearFilters,
  onRetry,
}: CatalogGridProps) {
  if (isLoading) {
    return <SkeletonGrid />;
  }

  if (isError) {
    return (
      <EmptyState
        title="Erro ao carregar o catálogo"
        description="Não foi possível conectar ao servidor. Tente novamente."
        icon="wifi-off"
        onRetry={onRetry}
        actionLabel="Tentar novamente"
      />
    );
  }

  if (total === 0) {
    return (
      <EmptyState
        title="Nenhuma raquete encontrada"
        description="Tente ajustar os filtros para ver mais opções."
        icon="search"
        onRetry={onClearFilters}
        actionLabel="Limpar filtros"
      />
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {paddles.map((paddle, i) => (
        <CatalogPaddleCard key={paddle.id} paddle={paddle} index={i} />
      ))}
    </div>
  );
}
