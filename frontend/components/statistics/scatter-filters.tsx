'use client';

import { useMemo, useState } from 'react';
import { Filter, X, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

export interface ScatterFilters {
    brand: string | null;
    priceRange: [number, number];
    coreThickness: string | null;
    minPower: number;
}

interface ScatterFiltersProps {
    brands: string[];
    priceRange: [number, number];
    filters: ScatterFilters;
    onFiltersChange: (filters: ScatterFilters) => void;
    activeCount: number;
    totalCount: number;
}

const CORE_OPTIONS = [
    { value: 'all', label: 'Todos' },
    { value: '14', label: '14mm (Power)' },
    { value: '16', label: '16mm (Control)' },
];

export function ScatterFiltersToolbar({
    brands,
    priceRange,
    filters,
    onFiltersChange,
    activeCount,
    totalCount,
}: ScatterFiltersProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    const hasActiveFilters = useMemo(() => {
        return (
            filters.brand !== null ||
            filters.coreThickness !== null ||
            filters.minPower > 0 ||
            filters.priceRange[0] !== priceRange[0] ||
            filters.priceRange[1] !== priceRange[1]
        );
    }, [filters, priceRange]);

    const resetFilters = () => {
        onFiltersChange({
            brand: null,
            priceRange: priceRange,
            coreThickness: null,
            minPower: 0,
        });
    };

    const formatPrice = (value: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            maximumFractionDigits: 0,
        }).format(value);
    };

    return (
        <div className="bg-card/50 backdrop-blur-sm border border-border/50 rounded-2xl p-4 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
                >
                    <Filter className="w-4 h-4" />
                    <span>Filtros</span>
                    {hasActiveFilters && (
                        <Badge variant="secondary" className="bg-primary/10 text-primary text-[10px]">
                            Ativos
                        </Badge>
                    )}
                </button>

                <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                        Mostrando <span className="font-bold text-foreground">{activeCount}</span> de {totalCount}
                    </span>

                    {hasActiveFilters && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={resetFilters}
                            className="h-7 text-xs gap-1"
                        >
                            <RotateCcw className="w-3 h-3" />
                            Reset
                        </Button>
                    )}
                </div>
            </div>

            {/* Filters Panel */}
            {isExpanded && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-border/50">
                    {/* Brand Filter */}
                    <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Marca
                        </label>
                        <Select
                            value={filters.brand || 'all'}
                            onValueChange={(value) =>
                                onFiltersChange({ ...filters, brand: value === 'all' ? null : value })
                            }
                        >
                            <SelectTrigger className="h-9 rounded-xl">
                                <SelectValue placeholder="Todas as marcas" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Todas as marcas</SelectItem>
                                {brands.map((brand) => (
                                    <SelectItem key={brand} value={brand}>
                                        {brand}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Core Thickness Filter */}
                    <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Núcleo
                        </label>
                        <Select
                            value={filters.coreThickness || 'all'}
                            onValueChange={(value) =>
                                onFiltersChange({ ...filters, coreThickness: value === 'all' ? null : value })
                            }
                        >
                            <SelectTrigger className="h-9 rounded-xl">
                                <SelectValue placeholder="Todas espessuras" />
                            </SelectTrigger>
                            <SelectContent>
                                {CORE_OPTIONS.map((option) => (
                                    <SelectItem key={option.value} value={option.value}>
                                        {option.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Price Range Filter */}
                    <div className="space-y-2 md:col-span-2">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Faixa de Preço
                            </label>
                            <span className="text-xs font-mono text-foreground">
                                {formatPrice(filters.priceRange[0])} - {formatPrice(filters.priceRange[1])}
                            </span>
                        </div>
                        <Slider
                            value={filters.priceRange}
                            min={priceRange[0]}
                            max={priceRange[1]}
                            step={50}
                            onValueChange={(value) =>
                                onFiltersChange({ ...filters, priceRange: value as [number, number] })
                            }
                            className="py-2"
                        />
                    </div>
                </div>
            )}

            {/* Quick Filters (always visible) */}
            <div className="flex flex-wrap gap-2">
                <QuickFilter
                    label="Power > 8"
                    active={filters.minPower >= 8}
                    onClick={() =>
                        onFiltersChange({ ...filters, minPower: filters.minPower >= 8 ? 0 : 8 })
                    }
                />
                <QuickFilter
                    label="14mm"
                    active={filters.coreThickness === '14'}
                    onClick={() =>
                        onFiltersChange({
                            ...filters,
                            coreThickness: filters.coreThickness === '14' ? null : '14'
                        })
                    }
                />
                <QuickFilter
                    label="16mm"
                    active={filters.coreThickness === '16'}
                    onClick={() =>
                        onFiltersChange({
                            ...filters,
                            coreThickness: filters.coreThickness === '16' ? null : '16'
                        })
                    }
                />
                <QuickFilter
                    label="< R$1000"
                    active={filters.priceRange[1] <= 1000}
                    onClick={() =>
                        onFiltersChange({
                            ...filters,
                            priceRange: filters.priceRange[1] <= 1000
                                ? priceRange
                                : [priceRange[0], 1000]
                        })
                    }
                />
            </div>
        </div>
    );
}

function QuickFilter({
    label,
    active,
    onClick
}: {
    label: string;
    active: boolean;
    onClick: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className={cn(
                'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
                'border border-border/50 hover:border-primary/50',
                active
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background hover:bg-muted/50'
            )}
        >
            {label}
            {active && <X className="w-3 h-3 inline ml-1" />}
        </button>
    );
}
