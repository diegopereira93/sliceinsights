"use client";

import React from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";

interface HistoryPoint {
    date: string;
    price_brl: number;
    is_available: boolean;
}

interface PriceHistoryChartProps {
    history: Record<string, HistoryPoint[]>;
}

export const PriceHistoryChart: React.FC<PriceHistoryChartProps> = ({ history }) => {
    // Transform data for Recharts (merge by date)
    const allDates = Array.from(
        new Set(
            Object.values(history)
                .flat()
                .map((p) => p.date)
        )
    ).sort();

    const chartData = allDates.map((date) => {
        const point: any = { date };
        Object.entries(history).forEach(([store, points]) => {
            const match = points.find((p) => p.date === date);
            if (match) {
                point[store] = match.price_brl;
            }
        });
        return point;
    });

    const stores = Object.keys(history);
    const colors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b"];

    if (chartData.length === 0) {
        return (
            <div className="h-48 flex items-center justify-center text-zinc-500 text-sm italic">
                Sem dados históricos disponíveis para este modelo ainda.
            </div>
        );
    }

    return (
        <div className="w-full h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                    <XAxis
                        dataKey="date"
                        stroke="#71717a"
                        fontSize={10}
                        tickFormatter={(str) => {
                            const d = new Date(str);
                            return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
                        }}
                    />
                    <YAxis
                        stroke="#71717a"
                        fontSize={10}
                        tickFormatter={(value) => `R$${value}`}
                        domain={["auto", "auto"]}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", fontSize: "12px" }}
                        itemStyle={{ fontSize: "12px" }}
                        labelStyle={{ color: "#a1a1aa", marginBottom: "4px" }}
                    />
                    <Legend wrapperStyle={{ fontSize: "10px", color: "#a1a1aa" }} />
                    {stores.map((store, index) => (
                        <Line
                            key={store}
                            type="monotone"
                            dataKey={store}
                            name={store}
                            stroke={colors[index % colors.length]}
                            strokeWidth={2}
                            dot={{ r: 3 }}
                            activeDot={{ r: 5 }}
                            connectNulls
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
