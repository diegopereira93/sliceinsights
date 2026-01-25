'use client';

import { Paddle } from '@/components/paddle/paddle-card';
import { useMemo } from 'react';
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend,
    BarChart, Bar, XAxis, YAxis, CartesianGrid, LabelList
} from 'recharts';
import { Check, Ruler, Layers, Medal, Box } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface TechnicalSpecsChartsProps {
    paddles: Paddle[];
}

const COLORS = ['#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#3b82f6', '#ec4899', '#6366f1', '#14b8a6'];
const RADIAN = Math.PI / 180;

const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }: any) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return percent > 0.05 ? (
        <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" className="text-xs font-bold font-mono">
            {`${(percent * 100).toFixed(0)}%`}
        </text>
    ) : null;
};

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-background/95 backdrop-blur-md border border-border p-3 rounded-xl shadow-xl text-xs z-50">
                <p className="font-bold text-sm mb-1">{data.name}</p>
                <div className="flex justify-between gap-4">
                    <span>Quantidade:</span>
                    <span className="font-mono font-bold text-primary">{data.value} raquetes</span>
                </div>
            </div>
        );
    }
    return null;
};

export function TechnicalSpecsCharts({ paddles }: TechnicalSpecsChartsProps) {

    // 1. Core Thickness Distribution
    const coreThicknessData = useMemo(() => {
        const counts: Record<string, number> = {};
        let total = 0;

        paddles.forEach(p => {
            const core = p.coreThicknessmm;
            if (core) {
                const key = `${core}mm`;
                counts[key] = (counts[key] || 0) + 1;
                total++;
            }
        });

        const threshold = 0.03; // 3%
        const groupedData: { name: string; value: number }[] = [];
        let othersCount = 0;

        Object.entries(counts).forEach(([name, value]) => {
            if (value / total < threshold) {
                othersCount += value;
            } else {
                groupedData.push({ name, value });
            }
        });

        // Sort main entries
        groupedData.sort((a, b) => b.value - a.value);

        // Append 'Outros' if any
        if (othersCount > 0) {
            groupedData.push({ name: 'Outros', value: othersCount });
        }

        return groupedData;
    }, [paddles]);

    // 2. Handle Length Analysis (Standard vs Elongated)
    const handleLengthData = useMemo(() => {
        const buckets = {
            'Curto (< 5.25")': 0,
            'Standard (5.25-5.4")': 0,
            'Híbrido (5.5")': 0,
            'Longo (> 5.5")': 0
        };

        paddles.forEach(p => {
            if (p.handleLength) {
                const len = parseFloat(p.handleLength);
                if (!isNaN(len)) {
                    if (len < 5.25) buckets['Curto (< 5.25")']++;
                    else if (len < 5.5) buckets['Standard (5.25-5.4")']++;
                    else if (len === 5.5) buckets['Híbrido (5.5")']++;
                    else buckets['Longo (> 5.5")']++;
                }
            }
        });

        return Object.entries(buckets).map(([name, value]) => ({ name, value }));
    }, [paddles]);

    // 3. Brand Market Share (Top 10)
    const brandShareData = useMemo(() => {
        const counts: Record<string, number> = {};
        paddles.forEach(p => {
            counts[p.brand] = (counts[p.brand] || 0) + 1;
        });

        return Object.entries(counts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10); // Check top 10
    }, [paddles]);


    return (
        <div className="space-y-12">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-slate-900 rounded-lg text-white">
                    <Layers className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Deep Dive Técnico</h2>
                    <p className="text-muted-foreground">Análise profunda das especificações de construção.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* 1. Core Thickness */}
                <div className="bg-card border border-border/50 rounded-3xl p-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-6">
                        <Box className="w-5 h-5 text-purple-500" />
                        <h3 className="font-bold text-lg">Espessura do Núcleo</h3>
                    </div>

                    <div className="h-[250px] w-full relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={coreThicknessData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={renderCustomizedLabel}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {coreThicknessData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.name === 'Outros' ? '#94a3b8' : COLORS[index % COLORS.length]}
                                        />
                                    ))}
                                </Pie>
                                <RechartsTooltip content={<CustomTooltip />} />
                                <Legend verticalAlign="bottom" height={36} iconType="circle" />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <p className="text-xs text-muted-foreground mt-4 text-center">
                        <strong>16mm</strong> domina o mercado (Controle), seguido por <strong>14mm</strong> (Potência).
                    </p>
                </div>

                {/* 2. Handle Length */}
                <div className="bg-card border border-border/50 rounded-3xl p-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-6">
                        <Ruler className="w-5 h-5 text-amber-500" />
                        <h3 className="font-bold text-lg">Tamanho do Cabo</h3>
                    </div>

                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={handleLengthData} layout="vertical" margin={{ left: 40, right: 30 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
                                <XAxis type="number" hide />
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    width={100}
                                    tick={{ fontSize: 10 }}
                                    interval={0}
                                />
                                <RechartsTooltip
                                    cursor={{ fill: 'transparent' }}
                                    content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            return (
                                                <div className="bg-slate-900 text-white text-xs p-2 rounded">
                                                    {payload[0].value} raquetes
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <Bar dataKey="value" fill="#f59e0b" radius={[0, 4, 4, 0]} barSize={30}>
                                    <LabelList dataKey="value" position="right" className="fill-foreground font-mono font-bold text-xs" />
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <p className="text-xs text-muted-foreground mt-4 text-center">
                        Cabos <strong>5.5"</strong> (Híbridos) são os favoritos para backhand de duas mãos.
                    </p>
                </div>

                {/* 3. Brand Presence */}
                <div className="bg-card border border-border/50 rounded-3xl p-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-6">
                        <Medal className="w-5 h-5 text-blue-500" />
                        <h3 className="font-bold text-lg">Top Marcas (Catálogo)</h3>
                    </div>

                    <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={brandShareData} margin={{ top: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis
                                    dataKey="name"
                                    tick={{ fontSize: 9 }}
                                    interval={0}
                                    angle={-45}
                                    textAnchor="end"
                                    height={60}
                                />
                                <YAxis hide />
                                <RechartsTooltip content={<CustomTooltip />} />
                                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                                    <LabelList dataKey="value" position="top" className="fill-foreground font-mono font-bold text-xs" />
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
