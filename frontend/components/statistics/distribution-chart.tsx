"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';
import { useMemo } from 'react';

interface DistributionChartProps {
    data: number[]; // Raw values to bin
    title: string;
    unit: string;
    color: string;
    binCount?: number;
    domain?: [number, number];
}

export function DistributionChart({ data, title, unit, color, binCount = 10, domain }: DistributionChartProps) {
    const chartData = useMemo(() => {
        if (!data.length) return [];

        const min = domain ? domain[0] : Math.min(...data);
        const max = domain ? domain[1] : Math.max(...data);
        const range = max - min;

        // Avoid division by zero
        if (range === 0) return [{ bin: min.toString(), count: data.length, label: `${min}` }];

        const step = range / binCount;
        const bins = Array.from({ length: binCount }, (_, i) => ({
            min: min + i * step,
            max: min + (i + 1) * step,
            count: 0,
            label: `${(min + i * step).toFixed(1)} - ${(min + (i + 1) * step).toFixed(1)}`
        }));

        data.forEach(val => {
            // Clamp value to range
            if (val < min || val > max) return;
            const index = Math.min(Math.floor((val - min) / step), binCount - 1);
            bins[index].count++;
        });

        // Format label for display (e.g., "7.8-8.0")
        return bins.map(b => ({
            name: b.label,
            count: b.count,
            range: [b.min, b.max]
        }));

    }, [data, binCount, domain]);

    return (
        <div className="bg-card border border-border/50 rounded-3xl p-5 shadow-sm h-full flex flex-col">
            <h3 className="font-bold text-sm uppercase tracking-wider text-muted-foreground mb-4">
                {title}
            </h3>
            <div className="flex-1 w-full min-h-[160px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 0, right: 0, left: -25, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.1} />
                        <XAxis
                            dataKey="name"
                            tick={{ fontSize: 9, fill: '#888' }}
                            interval={Math.floor(binCount / 3)}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            tick={{ fontSize: 9, fill: '#888' }}
                            tickLine={false}
                            axisLine={false}
                            allowDecimals={false}
                        />
                        <Tooltip
                            cursor={{ fill: 'transparent' }}
                            contentStyle={{
                                backgroundColor: 'hsl(var(--background))',
                                border: '1px solid hsl(var(--border))',
                                borderRadius: '8px',
                                fontSize: '12px'
                            }}
                            formatter={(value: any) => [value, 'Raquetes']}
                            labelFormatter={(label) => `${label} ${unit}`}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={color} fillOpacity={0.6 + (entry.count / Math.max(...chartData.map(d => d.count)) * 0.4)} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
