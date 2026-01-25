'use client';

import { useMemo } from 'react';
import { Paddle } from '@/components/paddle/paddle-card';
import {
    ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend
} from 'recharts';
import { motion } from 'framer-motion';
import { Building2, TrendingUp, Award } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface BrandIntelligenceProps {
    paddles: Paddle[];
    onBrandClick?: (brand: string) => void;
}

interface BrandStats {
    name: string;
    count: number;
    avgPrice: number;
    avgPower: number;
    avgSpin: number;
    avgSwingWeight: number;
    avgTwistWeight: number;
    avgRating: number;
    performanceScore: number;
    specialization: string;
    specializationColor: string;
}

const COLORS = ['#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#3b82f6', '#ec4899', '#6366f1', '#14b8a6', '#f97316', '#84cc16'];

function calculateBrandStats(brand: string, paddles: Paddle[]): BrandStats {
    const brandPaddles = paddles.filter(p => p.brand === brand);
    const count = brandPaddles.length;

    if (count === 0) {
        return {
            name: brand,
            count: 0,
            avgPrice: 0,
            avgPower: 0,
            avgSpin: 0,
            avgSwingWeight: 0,
            avgTwistWeight: 0,
            avgRating: 0,
            performanceScore: 0,
            specialization: 'N/A',
            specializationColor: 'text-gray-500',
        };
    }

    const avgPrice = brandPaddles.reduce((acc, p) => acc + p.price, 0) / count;

    const paddlesWithPower = brandPaddles.filter(p => p.power > 0);
    const avgPower = paddlesWithPower.length
        ? paddlesWithPower.reduce((acc, p) => acc + p.power, 0) / paddlesWithPower.length
        : 5;

    const paddlesWithSpin = brandPaddles.filter(p => p.spin > 0);
    const avgSpin = paddlesWithSpin.length
        ? paddlesWithSpin.reduce((acc, p) => acc + p.spin, 0) / paddlesWithSpin.length
        : 5;

    const paddlesWithSW = brandPaddles.filter(p => p.swingWeight);
    const avgSwingWeight = paddlesWithSW.length
        ? paddlesWithSW.reduce((acc, p) => acc + (p.swingWeight || 0), 0) / paddlesWithSW.length
        : 110;

    const paddlesWithTW = brandPaddles.filter(p => p.twistWeight);
    const avgTwistWeight = paddlesWithTW.length
        ? paddlesWithTW.reduce((acc, p) => acc + (p.twistWeight || 0), 0) / paddlesWithTW.length
        : 6;

    const paddlesWithRating = brandPaddles.filter(p => p.rating > 0);
    const avgRating = paddlesWithRating.length
        ? paddlesWithRating.reduce((acc, p) => acc + p.rating, 0) / paddlesWithRating.length
        : 7;

    // Calculate performance score (normalized)
    const performanceScore = (avgPower * 0.3 + avgSpin * 0.3 + (avgTwistWeight - 5) * 2 + (avgRating - 5)) / 3;

    // Determine specialization
    let specialization = 'Balanceada';
    let specializationColor = 'text-blue-500';

    if (avgPower > 7.5) {
        specialization = '⚡ Power';
        specializationColor = 'text-amber-500';
    } else if (avgSpin > 7.5) {
        specialization = '🌀 Spin';
        specializationColor = 'text-purple-500';
    } else if (avgSwingWeight < 108) {
        specialization = '🪶 Leve';
        specializationColor = 'text-emerald-500';
    } else if (avgTwistWeight > 6.8) {
        specialization = '🎯 Estável';
        specializationColor = 'text-pink-500';
    }

    return {
        name: brand,
        count,
        avgPrice,
        avgPower,
        avgSpin,
        avgSwingWeight,
        avgTwistWeight,
        avgRating,
        performanceScore,
        specialization,
        specializationColor,
    };
}

// Custom Tooltip for Brand Scatter
const BrandTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload as BrandStats;
        return (
            <div className="bg-background/95 backdrop-blur-md border border-border p-4 rounded-xl shadow-xl text-xs z-50">
                <p className="font-bold text-base mb-2">{data.name}</p>
                <div className="space-y-1">
                    <p className="flex justify-between gap-4">
                        <span className="text-muted-foreground">Raquetes:</span>
                        <span className="font-bold">{data.count}</span>
                    </p>
                    <p className="flex justify-between gap-4">
                        <span className="text-muted-foreground">Preço Médio:</span>
                        <span className="font-mono font-bold text-primary">
                            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(data.avgPrice)}
                        </span>
                    </p>
                    <p className="flex justify-between gap-4">
                        <span className="text-muted-foreground">Performance:</span>
                        <span className="font-bold">{data.performanceScore.toFixed(1)}</span>
                    </p>
                    <div className="pt-2 border-t border-border/50 mt-2">
                        <Badge variant="secondary" className={cn('text-xs', data.specializationColor)}>
                            {data.specialization}
                        </Badge>
                    </div>
                </div>
            </div>
        );
    }
    return null;
};

export function BrandIntelligence({ paddles, onBrandClick }: BrandIntelligenceProps) {
    const brandStats = useMemo(() => {
        const brands = [...new Set(paddles.map(p => p.brand))];
        return brands
            .map(brand => calculateBrandStats(brand, paddles))
            .filter(b => b.count >= 2) // At least 2 paddles
            .sort((a, b) => b.count - a.count)
            .slice(0, 10); // Top 10
    }, [paddles]);

    // Data for radar chart (top 3 brands)
    const radarData = useMemo(() => {
        const top3 = brandStats.slice(0, 3);
        if (top3.length === 0) return [];

        const metrics = ['Power', 'Spin', 'Estabilidade', 'Value'];
        return metrics.map(metric => {
            const point: any = { metric };
            top3.forEach((brand, index) => {
                let value = 5;
                switch (metric) {
                    case 'Power':
                        value = brand.avgPower;
                        break;
                    case 'Spin':
                        value = brand.avgSpin;
                        break;
                    case 'Estabilidade':
                        value = (brand.avgTwistWeight - 5) * 2 + 5; // Normalize to 0-10 scale
                        break;
                    case 'Value':
                        value = brand.avgRating > 0 ? (brand.avgRating / (brand.avgPrice / 1000)) : 5;
                        break;
                }
                point[brand.name] = Math.min(10, Math.max(0, value));
            });
            return point;
        });
    }, [brandStats]);

    // Position Scatter data
    const positionData = useMemo(() => {
        return brandStats.map(b => ({
            ...b,
            x: b.avgPrice,
            y: b.performanceScore,
            z: b.count * 5, // Bubble size
        }));
    }, [brandStats]);

    if (brandStats.length === 0) return null;

    return (
        <section className="space-y-8">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-indigo-500/10 to-blue-600/10 rounded-xl">
                    <Building2 className="w-6 h-6 text-indigo-500" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Brand Intelligence</h2>
                    <p className="text-xs text-muted-foreground">
                        Análise comparativa das principais marcas do catálogo.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Brand Positioning Scatter */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-card border border-border/50 rounded-3xl p-6 shadow-sm"
                >
                    <div className="flex items-center gap-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-indigo-500" />
                        <h3 className="font-bold text-lg">Posicionamento de Mercado</h3>
                    </div>
                    <p className="text-xs text-muted-foreground mb-4">
                        Preço médio (X) vs Performance média (Y). Tamanho = número de raquetes.
                    </p>

                    <div className="h-[280px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                                <XAxis
                                    type="number"
                                    dataKey="x"
                                    name="Preço"
                                    tick={{ fontSize: 10, fill: '#888' }}
                                    tickFormatter={(val) => `R$${(val / 1000).toFixed(1)}k`}
                                    domain={['dataMin - 100', 'dataMax + 100']}
                                    label={{ value: 'Preço Médio', position: 'insideBottom', offset: -10, fontSize: 10, fill: '#666' }}
                                />
                                <YAxis
                                    type="number"
                                    dataKey="y"
                                    name="Performance"
                                    tick={{ fontSize: 10, fill: '#888' }}
                                    domain={[0, 'dataMax + 1']}
                                    label={{ value: 'Performance', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10, fill: '#666' }}
                                />
                                <Tooltip content={<BrandTooltip />} />
                                <Scatter
                                    data={positionData}
                                    onClick={(data) => onBrandClick?.(data.name)}
                                    className="cursor-pointer"
                                >
                                    {positionData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={COLORS[index % COLORS.length]}
                                            fillOpacity={0.7}
                                            r={Math.min(20, Math.max(8, entry.count * 2))}
                                        />
                                    ))}
                                </Scatter>
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Radar Chart - Top 3 Brands */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-card border border-border/50 rounded-3xl p-6 shadow-sm"
                >
                    <div className="flex items-center gap-2 mb-4">
                        <Award className="w-5 h-5 text-amber-500" />
                        <h3 className="font-bold text-lg">Top 3 Marcas - Comparativo</h3>
                    </div>
                    <p className="text-xs text-muted-foreground mb-4">
                        Radar comparando Power, Spin, Estabilidade e Value Score.
                    </p>

                    <div className="h-[280px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart data={radarData}>
                                <PolarGrid stroke="#e5e7eb" />
                                <PolarAngleAxis
                                    dataKey="metric"
                                    tick={{ fontSize: 11, fill: '#666' }}
                                />
                                <PolarRadiusAxis
                                    angle={30}
                                    domain={[0, 10]}
                                    tick={{ fontSize: 9, fill: '#888' }}
                                />
                                {brandStats.slice(0, 3).map((brand, index) => (
                                    <Radar
                                        key={brand.name}
                                        name={brand.name}
                                        dataKey={brand.name}
                                        stroke={COLORS[index]}
                                        fill={COLORS[index]}
                                        fillOpacity={0.2}
                                        strokeWidth={2}
                                    />
                                ))}
                                <Legend
                                    iconType="circle"
                                    wrapperStyle={{ fontSize: '12px' }}
                                />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>
            </div>

            {/* Brand Tags */}
            <div className="flex flex-wrap gap-3">
                {brandStats.map((brand, index) => (
                    <motion.button
                        key={brand.name}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => onBrandClick?.(brand.name)}
                        className={cn(
                            'px-4 py-2 rounded-full border border-border/50 bg-card',
                            'hover:border-primary/50 hover:shadow-md transition-all',
                            'flex items-center gap-2 text-sm'
                        )}
                    >
                        <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="font-medium">{brand.name}</span>
                        <Badge variant="secondary" className={cn('text-[10px]', brand.specializationColor)}>
                            {brand.specialization}
                        </Badge>
                        <span className="text-xs text-muted-foreground">({brand.count})</span>
                    </motion.button>
                ))}
            </div>
        </section>
    );
}
