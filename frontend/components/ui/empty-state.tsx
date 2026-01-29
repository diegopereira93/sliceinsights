'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Search, RefreshCcw, WifiOff } from 'lucide-react';

interface EmptyStateProps {
    title?: string;
    description?: string;
    icon?: 'search' | 'wifi-off';
    onRetry?: () => void;
    actionLabel?: string;
}

export function EmptyState({
    title = "Nenhuma raquete encontrada",
    description = "Tente ajustar seus filtros ou busca.",
    icon = 'search',
    onRetry,
    actionLabel = "Limpar filtros"
}: EmptyStateProps) {
    const Icon = icon === 'search' ? Search : WifiOff;

    return (
        <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="p-5 bg-muted/50 rounded-full mb-6 relative">
                <Icon className="w-12 h-12 text-muted-foreground/50" />
                <div className="absolute inset-0 bg-primary/5 rounded-full animate-ping opacity-20" />
            </div>
            <h3 className="text-2xl font-black mb-2 uppercase italic tracking-tighter">{title}</h3>
            <p className="text-muted-foreground text-sm max-w-xs mx-auto mb-8">{description}</p>
            {onRetry && (
                <Button
                    onClick={onRetry}
                    variant="outline"
                    className="border-primary text-primary hover:bg-primary hover:text-primary-foreground font-black rounded-full px-8 h-12 shadow-sm transition-all"
                >
                    {icon === 'wifi-off' ? <RefreshCcw className="w-4 h-4 mr-2" /> : null}
                    {actionLabel}
                </Button>
            )}
        </div>
    );
}
