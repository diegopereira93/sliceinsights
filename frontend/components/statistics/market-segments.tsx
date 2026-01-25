'use client';

import { useMemo } from 'react';
import { Paddle } from '@/components/paddle/paddle-card';
import { motion } from 'framer-motion';
import { TrendingDown, Scale, TrendingUp, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarketSegmentsProps {
    paddles: Paddle[];
    onSegmentClick?: (segment: 'budget' | 'midrange' | 'premium') => void;
}

interface SegmentStats {
    count: number;
    avgPrice: number;
    avgPower: number;
    avgSpin: number;
    avgSwingWeight: number;
    topPaddle?: Paddle;
}

const SEGMENT_CONFIG = {
    budget: {
        label: 'Budget',
        sublabel: '< R$ 800',
        icon: TrendingDown,
        color: 'emerald',
        bgGradient: 'from-emerald-500/10 to-emerald-600/5',
        borderColor: 'border-emerald-500/30',
        textColor: 'text-emerald-600',
        iconBg: 'bg-emerald-500/10',
    },
    midrange: {
        label: 'Mid-Range',
        sublabel: 'R$ 800 - 1.500',
        icon: Scale,
        color: 'blue',
        bgGradient: 'from-blue-500/10 to-blue-600/5',
        borderColor: 'border-blue-500/30',
        textColor: 'text-blue-600',
        iconBg: 'bg-blue-500/10',
    },
    premium: {
        label: 'Premium',
        sublabel: '> R$ 1.500',
        icon: TrendingUp,
        color: 'amber',
        bgGradient: 'from-amber-500/10 to-amber-600/5',
        borderColor: 'border-amber-500/30',
        textColor: 'text-amber-600',
        iconBg: 'bg-amber-500/10',
    },
};

function calculateSegmentStats(paddles: Paddle[]): SegmentStats {
    if (!paddles.length) {
        return { count: 0, avgPrice: 0, avgPower: 0, avgSpin: 0, avgSwingWeight: 0 };
    }

    const count = paddles.length;
    const avgPrice = paddles.reduce((acc, p) => acc + p.price, 0) / count;

    const paddlesWithPower = paddles.filter(p => p.power > 0);
    const avgPower = paddlesWithPower.length
        ? paddlesWithPower.reduce((acc, p) => acc + p.power, 0) / paddlesWithPower.length
        : 0;

    const paddlesWithSpin = paddles.filter(p => p.spin > 0);
    const avgSpin = paddlesWithSpin.length
        ? paddlesWithSpin.reduce((acc, p) => acc + p.spin, 0) / paddlesWithSpin.length
        : 0;

    const paddlesWithSW = paddles.filter(p => p.swingWeight);
    const avgSwingWeight = paddlesWithSW.length
        ? paddlesWithSW.reduce((acc, p) => acc + (p.swingWeight || 0), 0) / paddlesWithSW.length
        : 0;

    // Top paddle by rating or power
    const topPaddle = [...paddles].sort((a, b) => (b.rating || 0) - (a.rating || 0))[0];

    return { count, avgPrice, avgPower, avgSpin, avgSwingWeight, topPaddle };
}

export function MarketSegments({ paddles, onSegmentClick }: MarketSegmentsProps) {
    const segments = useMemo(() => {
        const budget = paddles.filter(p => p.price > 0 && p.price < 800);
        const midrange = paddles.filter(p => p.price >= 800 && p.price <= 1500);
        const premium = paddles.filter(p => p.price > 1500);

        return {
            budget: calculateSegmentStats(budget),
            midrange: calculateSegmentStats(midrange),
            premium: calculateSegmentStats(premium),
        };
    }, [paddles]);

    const totalCount = paddles.filter(p => p.price > 0).length;

    return (
        <section className="space-y-6">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-violet-500/10 to-purple-600/10 rounded-xl">
                    <Sparkles className="w-6 h-6 text-violet-500" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Segmentos de Mercado</h2>
                    <p className="text-xs text-muted-foreground">
                        Compare as características médias por faixa de preço.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(Object.keys(SEGMENT_CONFIG) as Array<keyof typeof SEGMENT_CONFIG>).map((key, index) => {
                    const config = SEGMENT_CONFIG[key];
                    const stats = segments[key];
                    const Icon = config.icon;
                    const percentage = totalCount > 0 ? ((stats.count / totalCount) * 100).toFixed(0) : 0;

                    return (
                        <motion.div
                            key={key}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            onClick={() => onSegmentClick?.(key)}
                            className={cn(
                                'bg-gradient-to-br rounded-3xl p-6 border shadow-sm cursor-pointer',
                                'hover:shadow-md hover:scale-[1.02] transition-all duration-200',
                                config.bgGradient,
                                config.borderColor
                            )}
                        >
                            {/* Header */}
                            <div className="flex items-center justify-between mb-4">
                                <div className={cn('p-2 rounded-xl', config.iconBg)}>
                                    <Icon className={cn('w-5 h-5', config.textColor)} />
                                </div>
                                <span className={cn('text-2xl font-black', config.textColor)}>
                                    {percentage}%
                                </span>
                            </div>

                            {/* Title */}
                            <div className="mb-4">
                                <h3 className="font-bold text-lg leading-tight">{config.label}</h3>
                                <p className="text-xs text-muted-foreground">{config.sublabel}</p>
                            </div>

                            {/* Stats */}
                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-muted-foreground">Raquetes</span>
                                    <span className="font-mono font-bold text-sm">{stats.count}</span>
                                </div>

                                {stats.avgPower > 0 && (
                                    <div className="flex justify-between items-center">
                                        <span className="text-xs text-muted-foreground">Power Médio</span>
                                        <span className="font-mono text-sm">{stats.avgPower.toFixed(1)}</span>
                                    </div>
                                )}

                                {stats.avgSwingWeight > 0 && (
                                    <div className="flex justify-between items-center">
                                        <span className="text-xs text-muted-foreground">Swing Weight</span>
                                        <span className="font-mono text-sm">{stats.avgSwingWeight.toFixed(0)}</span>
                                    </div>
                                )}
                            </div>

                            {/* Top Paddle */}
                            {stats.topPaddle && (
                                <div className="mt-4 pt-4 border-t border-border/30">
                                    <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-1">
                                        Destaque
                                    </p>
                                    <p className="text-sm font-medium truncate">
                                        {stats.topPaddle.name}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        {stats.topPaddle.brand}
                                    </p>
                                </div>
                            )}
                        </motion.div>
                    );
                })}
            </div>
        </section>
    );
}
