'use client';

import {
    Radar,
    RadarChart as RechartsRadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip,
} from 'recharts';

interface RadarDataPoint {
    subject: string;
    value: number;
    fullMark: number;
}

interface RadarChartProps {
    data: RadarDataPoint[];
    className?: string;
}

export function RadarChart({ data, className }: RadarChartProps) {
    return (
        <div className={className}>
            <ResponsiveContainer width="100%" height={220}>
                <RechartsRadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
                    <PolarGrid
                        stroke="hsl(var(--muted-foreground))"
                        strokeOpacity={0.3}
                    />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{
                            fill: 'hsl(var(--foreground))',
                            fontSize: 11,
                            fontWeight: 600
                        }}
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 10]}
                        tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
                        tickCount={6}
                    />
                    <Radar
                        name="Performance"
                        dataKey="value"
                        stroke="#CEFF00"
                        fill="#CEFF00"
                        fillOpacity={0.35}
                        strokeWidth={2}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'hsl(var(--background))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                            fontSize: '12px',
                            fontWeight: 500,
                        }}
                        formatter={(value) => [`${value ?? 0}/10`, 'Rating']}
                    />
                </RechartsRadarChart>
            </ResponsiveContainer>
        </div>
    );
}
