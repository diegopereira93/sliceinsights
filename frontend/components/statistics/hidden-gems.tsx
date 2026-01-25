'use client';

import { useMemo } from 'react';
import { Paddle } from '@/components/paddle/paddle-card';
import { motion } from 'framer-motion';
import { Gem, TrendingUp, Star, Zap, Target, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface HiddenGemsProps {
    paddles: Paddle[];
    onPaddleClick?: (paddle: Paddle) => void;
    idealPoint?: { power: number; control: number; spin: number; } | null;
}

interface GemPaddle extends Paddle {
    gemReason: string;
    gemScore: number;
    gemIcon: React.ReactNode;
    gemColor: string;
}

export function HiddenGems({ paddles, onPaddleClick, idealPoint }: HiddenGemsProps) {
    const gems = useMemo(() => {
        if (!paddles.length) return [];

        const avgPrice = paddles.reduce((acc, p) => acc + p.price, 0) / paddles.length;
        const paddlesWithRating = paddles.filter(p => p.rating > 0);
        const avgRating = paddlesWithRating.length
            ? paddlesWithRating.reduce((acc, p) => acc + p.rating, 0) / paddlesWithRating.length
            : 7;

        const foundGems: GemPaddle[] = [];

        paddles.forEach(paddle => {
            // Critério 1: Alta avaliação + preço abaixo da média
            if (paddle.rating >= 8.5 && paddle.price < avgPrice && paddle.price > 0) {
                const valueFactor = (paddle.rating / (paddle.price / 1000));
                foundGems.push({
                    ...paddle,
                    gemReason: 'Alto Rating + Preço Justo',
                    gemScore: valueFactor,
                    gemIcon: <Star className="w-4 h-4" />,
                    gemColor: 'text-amber-500 bg-amber-500/10',
                });
            }

            // Critério 2: Alto Spin + preço competitivo
            if (paddle.spinRPM && paddle.spinRPM >= 1800 && paddle.price < avgPrice * 1.2) {
                foundGems.push({
                    ...paddle,
                    gemReason: 'Spin Excepcional',
                    gemScore: paddle.spinRPM / 100,
                    gemIcon: <Target className="w-4 h-4" />,
                    gemColor: 'text-blue-500 bg-blue-500/10',
                });
            }

            // Critério 3: Alto Twist Weight (estabilidade) + Swing Weight moderado (fácil de manejar)
            if (paddle.twistWeight && paddle.swingWeight &&
                paddle.twistWeight >= 6.5 && paddle.swingWeight <= 115) {
                foundGems.push({
                    ...paddle,
                    gemReason: 'Estável & Manejável',
                    gemScore: (paddle.twistWeight * 10) + (120 - paddle.swingWeight),
                    gemIcon: <Zap className="w-4 h-4" />,
                    gemColor: 'text-purple-500 bg-purple-500/10',
                });
            }

            // Critério 4: Value Score - melhor custo-benefício geral
            if (paddle.price > 0 && paddle.rating > 0) {
                const valueScore = (paddle.rating * 100) / (paddle.price / 100);
                if (valueScore > 1.5) {
                    foundGems.push({
                        ...paddle,
                        gemReason: 'Melhor Custo-Benefício',
                        gemScore: valueScore * 10,
                        gemIcon: <TrendingUp className="w-4 h-4" />,
                        gemColor: 'text-emerald-500 bg-emerald-500/10',
                    });
                }
            }
        });

        // Remove duplicatas (mesmo paddle pode ter múltiplos critérios)
        // Mantém apenas a razão com maior score
        const uniqueGems = Object.values(
            foundGems.reduce((acc, gem) => {
                if (!acc[gem.id] || acc[gem.id].gemScore < gem.gemScore) {
                    acc[gem.id] = gem;
                }
                return acc;
            }, {} as Record<string, GemPaddle>)
        );

        // Ordena por score e retorna top 5
        return uniqueGems
            .sort((a, b) => b.gemScore - a.gemScore)
            .slice(0, 5);
    }, [paddles]);

    if (!gems.length) return null;

    return (
        <section className="space-y-6">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-pink-500/10 to-rose-600/10 rounded-xl">
                    <Gem className="w-6 h-6 text-pink-500" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Joias Escondidas</h2>
                    <p className="text-xs text-muted-foreground">
                        Raquetes com combinação rara de qualidade e preço.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
                {gems.map((gem, index) => (
                    <motion.div
                        key={gem.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        onClick={() => onPaddleClick?.(gem)}
                        className={cn(
                            'bg-card border border-border/50 rounded-2xl p-4 cursor-pointer',
                            'hover:shadow-lg hover:border-pink-500/30 transition-all duration-200',
                            'flex items-center gap-4 group'
                        )}
                    >
                        {/* Rank */}
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center">
                            <span className="text-white font-bold text-sm">{index + 1}</span>
                        </div>

                        {/* Image placeholder */}
                        {gem.image ? (
                            <img
                                src={gem.image}
                                alt={gem.name}
                                className="w-12 h-12 object-contain rounded-lg bg-muted/30"
                            />
                        ) : (
                            <div className="w-12 h-12 rounded-lg bg-muted/30 flex items-center justify-center">
                                <Gem className="w-6 h-6 text-muted-foreground/30" />
                            </div>
                        )}

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                                    {gem.brand}
                                </p>
                                <Badge variant="secondary" className={cn('text-[10px] px-2 py-0', gem.gemColor)}>
                                    {gem.gemIcon}
                                    <span className="ml-1">{gem.gemReason}</span>
                                </Badge>
                            </div>
                            <p className="font-bold text-sm truncate group-hover:text-pink-500 transition-colors">
                                {gem.name}
                            </p>
                            {idealPoint && (
                                <div className="mt-1 flex items-center gap-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                                    <span className="text-[10px] text-primary font-bold">Match para você</span>
                                </div>
                            )}
                        </div>

                        {/* Price & Rating */}
                        <div className="text-right flex-shrink-0">
                            <p className="font-black text-lg text-primary font-mono">
                                {new Intl.NumberFormat('pt-BR', {
                                    style: 'currency',
                                    currency: 'BRL',
                                    maximumFractionDigits: 0
                                }).format(gem.price)}
                            </p>
                            {gem.rating > 0 && (
                                <p className="text-xs text-muted-foreground flex items-center justify-end gap-1">
                                    <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
                                    {gem.rating.toFixed(1)}
                                </p>
                            )}
                        </div>

                        {/* Chevron */}
                        <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-pink-500 transition-all" />
                    </motion.div>
                ))}
            </div>
        </section>
    );
}
