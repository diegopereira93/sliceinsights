'use client';

import * as React from 'react';
import { HelpCircle } from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface InfoTooltipProps {
    term: string;
    children: React.ReactNode;
    className?: string;
    iconSize?: number;
}

// Definições de termos técnicos de pickleball
const TERM_DEFINITIONS: Record<string, { title: string; description: string; tip?: string }> = {
    'swing_weight': {
        title: 'Swing Weight',
        description: 'Mede como o peso está distribuído na raquete ao balançá-la. Quanto maior, mais "pesada" a raquete parece durante o swing.',
        tip: '< 110 = Leve | 110-120 = Equilibrada | > 120 = Pesada'
    },
    'twist_weight': {
        title: 'Twist Weight',
        description: 'Mede a estabilidade da raquete em batidas fora do centro. Maior twist weight = maior sweet spot e menos torção no impacto.',
        tip: '< 6.0 = Menos estável | > 6.5 = Muito estável'
    },
    'spin_rpm': {
        title: 'Spin (RPM)',
        description: 'Rotações por minuto que a raquete consegue gerar na bola. Superfícies texturizadas aumentam esse valor.',
        tip: '> 1800 RPM = Excelente para efeitos'
    },
    'power': {
        title: 'Power',
        description: 'Capacidade de gerar velocidade na bola. Raquetes mais longas e com núcleos finos (14mm) tendem a ter mais power.',
        tip: 'Ideal para: finalizações e smashes'
    },
    'control': {
        title: 'Control',
        description: 'Precisão e previsibilidade nas batidas. Raquetes com núcleos grossos (16mm) e mais leves oferecem mais controle.',
        tip: 'Ideal para: dinks, drops e jogadas na net'
    },
    'sweet_spot': {
        title: 'Sweet Spot',
        description: 'Área ideal de batida onde você obtém máxima potência e mínima vibração. Correlacionado com o Twist Weight.',
        tip: 'Maior sweet spot = mais perdão em batidas off-center'
    },
    'core_thickness': {
        title: 'Espessura do Núcleo',
        description: 'A espessura do honeycomb interno. 16mm = mais controle e toque. 14mm = mais potência e pop.',
        tip: '16mm para iniciantes/intermediários | 14mm para agressivos'
    },
    'handle_length': {
        title: 'Tamanho do Cabo',
        description: 'Comprimento da empunhadura. Cabos mais longos (5.5") facilitam backhand de duas mãos e dão mais alavanca.',
        tip: '5.5" = Híbrido | > 5.5" = Ideal para duas mãos'
    },
    'value_score': {
        title: 'Value Score',
        description: 'Pontuação de custo-benefício calculada dividindo a pontuação técnica pelo preço. Maior = melhor investimento.',
        tip: 'Joias escondidas têm alto value score!'
    },
};

export function InfoTooltip({ term, children, className, iconSize = 14 }: InfoTooltipProps) {
    const key = term.toLowerCase().replace(/\s+/g, '_');
    const definition = TERM_DEFINITIONS[key];

    if (!definition) {
        return <>{children}</>;
    }

    return (
        <TooltipProvider delayDuration={200}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <span className={cn('inline-flex items-center gap-1.5 cursor-help', className)}>
                        {children}
                        <HelpCircle
                            className="text-muted-foreground hover:text-primary transition-colors"
                            size={iconSize}
                        />
                    </span>
                </TooltipTrigger>
                <TooltipContent
                    side="top"
                    className="max-w-xs p-4 bg-background/95 backdrop-blur-md border border-border shadow-xl"
                >
                    <div className="space-y-2">
                        <p className="font-bold text-sm text-foreground">{definition.title}</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                            {definition.description}
                        </p>
                        {definition.tip && (
                            <div className="pt-2 border-t border-border/50">
                                <p className="text-xs font-medium text-primary">
                                    💡 {definition.tip}
                                </p>
                            </div>
                        )}
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}

// Versão simplificada para uso inline
export function QuickInfo({ term }: { term: string }) {
    const key = term.toLowerCase().replace(/\s+/g, '_');
    const definition = TERM_DEFINITIONS[key];

    if (!definition) return null;

    return (
        <TooltipProvider delayDuration={200}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <HelpCircle
                        className="inline-block ml-1 text-muted-foreground hover:text-primary transition-colors cursor-help"
                        size={12}
                    />
                </TooltipTrigger>
                <TooltipContent
                    side="top"
                    className="max-w-xs p-3 bg-background/95 backdrop-blur-md border border-border"
                >
                    <p className="text-xs text-muted-foreground">{definition.description}</p>
                    {definition.tip && (
                        <p className="text-xs font-medium text-primary mt-1">💡 {definition.tip}</p>
                    )}
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
