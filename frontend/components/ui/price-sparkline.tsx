'use client';

import { useMemo } from 'react';

interface PriceSparklineProps {
    paddleId: string;
    currentPrice: number;
    days?: number;
    className?: string;
}

export function PriceSparkline({ paddleId, currentPrice, days = 7, className }: PriceSparklineProps) {
    // Generate deterministic mock data based on paddleId
    const data = useMemo(() => {
        const points = [];
        const seed = paddleId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);

        // Pseudo-random function
        const random = (s: number) => {
            const x = Math.sin(s) * 10000;
            return x - Math.floor(x);
        };

        let lastPrice = currentPrice * (0.95 + random(seed) * 0.1); // Start slightly off

        for (let i = 0; i < days; i++) {
            const change = (random(seed + i) - 0.48) * (currentPrice * 0.02); // Small bias towards change
            lastPrice = lastPrice + change;
            points.push(lastPrice);
        }

        // Ensure the last point is the current price
        points[points.length - 1] = currentPrice;

        return points;
    }, [paddleId, currentPrice, days]);

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const padding = range * 0.1;

    const width = 100;
    const height = 30;

    const getX = (index: number) => (index / (data.length - 1)) * width;
    const getY = (value: number) => height - ((value - min) / range) * (height - 4) - 2;

    const pathData = data.reduce((acc, val, i) =>
        acc + (i === 0 ? `M ${getX(i)} ${getY(val)}` : ` L ${getX(i)} ${getY(val)}`),
        ''
    );

    const isUp = data[data.length - 1] > data[0];

    return (
        <div className={className}>
            <svg
                width="100%"
                height={height}
                viewBox={`0 0 ${width} ${height}`}
                preserveAspectRatio="none"
                className="overflow-visible"
            >
                <defs>
                    <linearGradient id={`gradient-${paddleId}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={isUp ? '#CEFF00' : '#FF4B4B'} stopOpacity="0.2" />
                        <stop offset="100%" stopColor={isUp ? '#CEFF00' : '#FF4B4B'} stopOpacity="0" />
                    </linearGradient>
                </defs>

                {/* Shadow/Fill Area */}
                <path
                    d={`${pathData} L ${getX(data.length - 1)} ${height} L 0 ${height} Z`}
                    fill={`url(#gradient-${paddleId})`}
                />

                {/* Main Line */}
                <path
                    d={pathData}
                    fill="none"
                    stroke={isUp ? '#CEFF00' : '#FF4B4B'}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="drop-shadow-[0_0_4px_rgba(206,255,0,0.3)]"
                />

                {/* End Point */}
                <circle
                    cx={getX(data.length - 1)}
                    cy={getY(data[data.length - 1])}
                    r="2"
                    fill={isUp ? '#CEFF00' : '#FF4B4B'}
                />
            </svg>
        </div>
    );
}
