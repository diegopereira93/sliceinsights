'use client';

import { useMemo, useState, useEffect } from 'react';
import { Paddle } from '@/components/paddle/paddle-card';
import {
    ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ZAxis, ReferenceLine, Label, Cell, Legend
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, Zap, Target, DollarSign, Activity, Shield, Scale, BarChart3, Wind, Trophy, Gem, Star, Award } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
    Drawer,
    DrawerContent,
    DrawerHeader,
    DrawerTitle,
    DrawerDescription,
    DrawerFooter,
} from "@/components/ui/drawer";
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PaddleCard } from '@/components/paddle/paddle-card';
import { LeaderboardCard, LeaderboardItem } from '@/components/statistics/leaderboard-card';
import { DistributionChart } from '@/components/statistics/distribution-chart';
import { TechnicalSpecsCharts } from '@/components/statistics/technical-specs-charts';
import { MarketSegments } from '@/components/statistics/market-segments';
import { HiddenGems } from '@/components/statistics/hidden-gems';
import { ScatterFiltersToolbar, ScatterFilters } from '@/components/statistics/scatter-filters';
import { BrandIntelligence } from '@/components/statistics/brand-intelligence';
import { InfoTooltip, QuickInfo } from '@/components/ui/info-tooltip';

interface StatisticsClientProps {
    initialPaddles: Paddle[];
}

interface UserProfile {
    answers: Record<string, string>;
    request: any;
    timestamp: string;
}

interface IdealPoint {
    power: number;
    control: number;
    spin: number;
    sweetSpot: number;
    price: number;
    rating: number;
}

// --- Custom Tooltip Component for Recharts ---
const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-background/95 backdrop-blur-md border border-border p-3 rounded-xl shadow-xl text-xs z-50">
                <p className="font-bold text-sm mb-1">{data.name}</p>
                <p className="text-muted-foreground mb-2">{data.brand}</p>
                <div className="space-y-1">
                    <p className="flex justify-between gap-4">
                        <span>Preço:</span>
                        <span className="font-mono font-bold text-primary">
                            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(data.price)}
                        </span>
                    </p>
                    <div className="w-full h-px bg-border my-1" />
                    {data.power !== undefined && <p className="flex justify-between gap-4"><span>Power:</span> <span>{data.power}</span></p>}
                    {data.control !== undefined && <p className="flex justify-between gap-4"><span>Control:</span> <span>{data.control}</span></p>}
                    {data.spin !== undefined && <p className="flex justify-between gap-4"><span>Spin:</span> <span>{data.spin}</span></p>}
                    {data.swingWeight && <p className="flex justify-between gap-4"><span>Swing Weight:</span> <span>{data.swingWeight}</span></p>}
                    {data.twistWeight && <p className="flex justify-between gap-4"><span>Twist Weight:</span> <span>{data.twistWeight}</span></p>}
                </div>
            </div>
        );
    }
    return null;
};

// Animation variants for stagger effect
const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.1 }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
};

export function StatisticsClient({ initialPaddles }: StatisticsClientProps) {
    const [selectedPaddle, setSelectedPaddle] = useState<Paddle | null>(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [scatterFilters, setScatterFilters] = useState<ScatterFilters>({
        brand: null,
        priceRange: [0, 3000],
        coreThickness: null,
        minPower: 0,
    });
    const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

    // --- Load User Profile from Quiz ---
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const savedSession = sessionStorage.getItem('slice_quiz_results');
            const savedLocal = localStorage.getItem('user_profile');

            if (savedSession) {
                try {
                    const parsed = JSON.parse(savedSession);
                    console.log("Statistics: Loaded user profile from sessionStorage", parsed);
                    setUserProfile(parsed);
                } catch (e) {
                    console.error("Failed to parse quiz results from sessionStorage", e);
                }
            } else if (savedLocal) {
                try {
                    const parsed = JSON.parse(savedLocal);
                    console.log("Statistics: Loaded user profile from localStorage", parsed);
                    // For backwards compatibility: if it doesn't have .request, it might be the request itself
                    if (parsed && !parsed.request && (parsed.skill_level || parsed.play_style)) {
                        setUserProfile({ request: parsed } as any);
                    } else {
                        setUserProfile(parsed);
                    }
                } catch (e) {
                    console.error("Failed to parse quiz results from localStorage", e);
                }
            } else {
                console.log("Statistics: No profile found in storage");
            }
        }
    }, []);

    useEffect(() => {
        console.log("Statistics: initialPaddles count", initialPaddles.length);
    }, [initialPaddles]);

    const idealPoint = useMemo<IdealPoint | null>(() => {
        if (!userProfile) return null;

        const req = userProfile.request;

        // Power vs Control
        let power = 5;
        if (req.power_preference_percent !== undefined) {
            power = req.power_preference_percent / 10;
        } else {
            if (req.play_style?.toLowerCase() === 'power') power = 8.5;
            if (req.play_style?.toLowerCase() === 'control') power = 3.5;
            if (req.play_style?.toLowerCase() === 'balanced') power = 6.0;
        }
        const control = 10 - power;

        // Spin
        let spin = 7;
        if (req.spin_preference === 'high') spin = 9.0;
        if (req.spin_preference === 'low') spin = 4.0;

        // Sweet Spot (Inferred from comfort/tennis elbow)
        let sweetSpot = 7;
        if (req.has_tennis_elbow) sweetSpot = 9.5;

        return {
            power,
            control,
            spin,
            sweetSpot,
            price: req.budget_max_brl || 3000,
            rating: 9.0 // Target for elite performance
        };
    }, [userProfile]);

    // --- Derived Data Calculations ---
    const stats = useMemo(() => {
        if (!initialPaddles.length) return null;

        const totalPaddles = initialPaddles.length;
        const avgPrice = initialPaddles.reduce((acc, p) => acc + p.price, 0) / totalPaddles;

        // Price range for filters
        const prices = initialPaddles.map(p => p.price).filter(p => p > 0);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);

        // Get unique brands
        const brands = [...new Set(initialPaddles.map(p => p.brand))].sort();

        // --- Dynamic Insights ---
        // 1. Best Value (highest rating / price ratio)
        const paddlesWithRating = initialPaddles.filter(p => p.rating > 0 && p.price > 0);
        const bestValue = paddlesWithRating.length ?
            [...paddlesWithRating].sort((a, b) => (b.rating / b.price) - (a.rating / a.price))[0] : null;

        // 2. Hidden Gem (high spin or power, below avg price)
        const hiddenGem = initialPaddles
            .filter(p => p.price < avgPrice && p.price > 0 && (p.spin > 7 || p.power > 7))
            .sort((a, b) => (b.spin + b.power) - (a.spin + a.power))[0] || null;

        // 3. Market Pattern - most common core thickness
        const coreCount: Record<string, number> = {};
        initialPaddles.forEach(p => {
            if (p.coreThicknessmm) {
                const key = `${p.coreThicknessmm}mm`;
                coreCount[key] = (coreCount[key] || 0) + 1;
            }
        });
        const mostCommonCore = Object.entries(coreCount).sort((a, b) => b[1] - a[1])[0];
        const corePercentage = mostCommonCore ? ((mostCommonCore[1] / totalPaddles) * 100).toFixed(0) : null;

        // 4. Top Power paddle
        const topPowerPaddle = [...initialPaddles].sort((a, b) => (b.powerOriginal || 0) - (a.powerOriginal || 0))[0];

        // Chart data maps
        const pricePerformanceData = initialPaddles
            .filter(p => p.rating > 0)
            .map(p => ({ ...p, priceJitter: p.price + (Math.random() * 20 - 10) }));

        const powerControlData = initialPaddles.map(p => {
            let control = p.control;
            let power = p.power;
            if ((!control || control === 0) && p.swingWeight) control = Math.max(0, Math.min(10, 10 - ((p.swingWeight - 100) / 3)));
            if ((!power || power === 0) && p.powerOriginal) power = Math.max(0, Math.min(10, p.powerOriginal));
            return { ...p, control, power };
        }).filter(p => p.power > 0 && p.control > 0).map(p => ({ ...p, x: p.power, y: p.control, z: 1 }));

        const physicsData = initialPaddles
            .filter(p => p.twistWeight && p.swingWeight)
            .map(p => ({ ...p, x: p.twistWeight, y: p.swingWeight, z: p.price }));

        const spinSweetSpotData = initialPaddles.map(p => {
            let sweetSpot = p.sweetSpot;
            if ((!sweetSpot || sweetSpot === 0) && p.twistWeight) sweetSpot = Math.max(0, Math.min(10, (p.twistWeight - 5.0) * 4));
            return { ...p, sweetSpot };
        }).filter(p => p.spin > 0 && p.sweetSpot > 0).map(p => ({ ...p, x: p.spin, y: p.sweetSpot, z: p.price }));

        // Leaderboards
        const getTop = (key: keyof Paddle, sortFn: (a: Paddle, b: Paddle) => number): LeaderboardItem[] => {
            return [...initialPaddles]
                .sort(sortFn)
                .slice(0, 10)
                .map((p, i) => ({
                    rank: i + 1,
                    paddle: p,
                    value: p[key] as number,
                    unit: ''
                }));
        };

        const topPower = getTop('powerOriginal', (a, b) => (b.powerOriginal || 0) - (a.powerOriginal || 0))
            .map(i => ({ ...i, value: (i.value as number)?.toFixed(1) || 'N/A' }));

        const topSpin = getTop('spinRPM', (a, b) => (b.spinRPM || 0) - (a.spinRPM || 0))
            .map(i => ({ ...i, unit: 'RPM' }));

        const topSwingWeight = getTop('swingWeight', (a, b) => (b.swingWeight || 0) - (a.swingWeight || 0));

        const topTwistWeight = getTop('twistWeight', (a, b) => (b.twistWeight || 0) - (a.twistWeight || 0))
            .map(i => ({ ...i, value: (i.value as number)?.toFixed(2) || 'N/A' }));

        // Distributions
        const swingWeights = initialPaddles.map(p => p.swingWeight).filter(v => v !== undefined) as number[];
        const twistWeights = initialPaddles.map(p => p.twistWeight).filter(v => v !== undefined) as number[];

        return {
            totalPaddles,
            avgPrice,
            minPrice,
            maxPrice,
            brands,
            // Dynamic insights
            bestValue,
            hiddenGem,
            mostCommonCore: mostCommonCore ? mostCommonCore[0] : null,
            corePercentage,
            topPowerPaddle,
            // Chart data
            pricePerformanceData,
            powerControlData,
            physicsData,
            spinSweetSpotData,
            leaderboards: { topPower, topSpin, topSwingWeight, topTwistWeight },
            distributions: { prices, swingWeights, twistWeights }
        };
    }, [initialPaddles]);

    // Apply scatter filters
    const filteredPaddles = useMemo(() => {
        return initialPaddles.filter(p => {
            if (scatterFilters.brand && p.brand !== scatterFilters.brand) return false;
            if (p.price < scatterFilters.priceRange[0] || p.price > scatterFilters.priceRange[1]) return false;
            if (scatterFilters.coreThickness) {
                const core = parseFloat(scatterFilters.coreThickness);
                if (p.coreThicknessmm !== core) return false;
            }
            if (scatterFilters.minPower > 0 && (p.power || 0) < scatterFilters.minPower) return false;
            return true;
        });
    }, [initialPaddles, scatterFilters]);

    // Initialize filter price range
    useEffect(() => {
        if (stats && scatterFilters.priceRange[1] === 3000) {
            setScatterFilters(f => ({
                ...f,
                priceRange: [stats.minPrice, stats.maxPrice]
            }));
        }
    }, [stats]);

    if (!stats) return <div className="p-8 text-center animate-pulse">Carregando dados do laboratório...</div>;

    // --- Match Score Calculation ---
    const matchScore = useMemo(() => {
        if (!selectedPaddle || !idealPoint) return null;

        const p = selectedPaddle;
        const i = idealPoint;

        // Euclidean distance for Power, Control, Spin
        const distance = Math.sqrt(
            Math.pow((p.power || 5) - i.power, 2) +
            Math.pow((p.control || 5) - i.control, 2) +
            Math.pow((p.spin || 5) - i.spin, 2)
        );

        // Max possible distance is sqrt(10^2 + 10^2 + 10^2) = 17.32
        const maxDist = 17.32;
        const score = Math.max(0, Math.min(100, 100 - (distance / maxDist * 100)));

        return Math.round(score);
    }, [selectedPaddle, idealPoint]);

    return (
        <div className="min-h-screen bg-background text-foreground">

            {/* Header */}
            <div className="px-6 py-10 bg-gradient-to-br from-muted/30 to-background border-b border-border/50 rounded-b-[2.5rem] mb-8">
                <div className="max-w-4xl mx-auto">
                    <Badge variant="secondary" className="mb-4">Data Analytics v3.0</Badge>
                    <h1 className="text-4xl md:text-5xl font-black tracking-tighter uppercase italic mb-4 bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/60">
                        Raio-X do Mercado
                    </h1>
                    <p className="text-muted-foreground text-lg max-w-lg leading-relaxed">
                        Visualizações baseadas em dados reais. Encontre a anomalia do mercado: <span className="text-primary font-bold">Alta Performance, Baixo Custo.</span>
                    </p>
                </div>
            </div>

            {/* User Profile Alert */}
            {userProfile && (
                <div className="px-4 max-w-5xl mx-auto -mt-4 mb-8">
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-primary/10 border border-primary/30 p-4 rounded-2xl flex items-center justify-between"
                    >
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/20 rounded-xl">
                                <Star className="w-5 h-5 text-primary stroke-[3px]" />
                            </div>
                            <div>
                                <p className="text-sm font-bold">Modo Personalizado Ativo</p>
                                <p className="text-[11px] text-muted-foreground">Exibindo seu <b>Ideal Spot</b> nos gráficos baseado no seu quiz.</p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-[10px] h-8 font-bold uppercase tracking-wider"
                            onClick={() => {
                                sessionStorage.removeItem('slice_quiz_results');
                                window.location.reload();
                            }}
                        >
                            Resetar
                        </Button>
                    </motion.div>
                </div>
            )}

            {/* Tabs Navigation */}
            <div className="px-4 max-w-5xl mx-auto mb-8">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-4 h-12 rounded-2xl bg-muted/50 p-1">
                        <TabsTrigger value="overview" className="rounded-xl data-[state=active]:bg-background data-[state=active]:shadow-sm">
                            Overview
                        </TabsTrigger>
                        <TabsTrigger value="comparativos" className="rounded-xl data-[state=active]:bg-background data-[state=active]:shadow-sm">
                            Comparativos
                        </TabsTrigger>
                        <TabsTrigger value="rankings" className="rounded-xl data-[state=active]:bg-background data-[state=active]:shadow-sm">
                            Rankings
                        </TabsTrigger>
                        <TabsTrigger value="marcas" className="rounded-xl data-[state=active]:bg-background data-[state=active]:shadow-sm">
                            Marcas
                        </TabsTrigger>
                    </TabsList>

                    {/* OVERVIEW TAB */}
                    <TabsContent value="overview" className="mt-8 space-y-12">
                        {/* Dynamic KPI Cards */}
                        <motion.div
                            variants={containerVariants}
                            initial="hidden"
                            animate="visible"
                            className="grid grid-cols-2 md:grid-cols-4 gap-4"
                        >
                            <motion.div variants={itemVariants} className="bg-card border border-border/50 p-6 rounded-3xl shadow-sm relative overflow-hidden group hover:scale-[1.02] transition-transform">
                                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                    <Activity className="w-16 h-16" />
                                </div>
                                <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-2">Database</p>
                                <p className="text-4xl font-black">{stats.totalPaddles}</p>
                                <p className="text-[10px] text-muted-foreground mt-1">Raquetes Analisadas</p>
                            </motion.div>

                            <motion.div variants={itemVariants} className="bg-card border border-border/50 p-6 rounded-3xl shadow-sm relative overflow-hidden group hover:scale-[1.02] transition-transform">
                                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                    <DollarSign className="w-16 h-16" />
                                </div>
                                <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-2">Preço Médio</p>
                                <p className="text-3xl font-black text-primary">
                                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(stats.avgPrice)}
                                </p>
                                <p className="text-[10px] text-muted-foreground mt-1">Investimento Médio</p>
                            </motion.div>

                            {stats.bestValue && (
                                <motion.div
                                    variants={itemVariants}
                                    onClick={() => setSelectedPaddle(stats.bestValue)}
                                    className="bg-card border border-emerald-500/30 p-6 rounded-3xl shadow-sm relative overflow-hidden group hover:scale-[1.02] transition-transform cursor-pointer hover:border-emerald-500/50"
                                >
                                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                        <Gem className="w-16 h-16" />
                                    </div>
                                    <p className="text-xs text-emerald-600 uppercase font-bold tracking-wider mb-2 flex items-center gap-1">
                                        <Gem className="w-3 h-3" /> Melhor Valor
                                    </p>
                                    <p className="text-lg font-bold truncate">{stats.bestValue.name}</p>
                                    <p className="text-[10px] text-muted-foreground mt-1">{stats.bestValue.brand}</p>
                                </motion.div>
                            )}

                            {stats.topPowerPaddle && (
                                <motion.div
                                    variants={itemVariants}
                                    onClick={() => setSelectedPaddle(stats.topPowerPaddle)}
                                    className="bg-card border border-amber-500/30 p-6 rounded-3xl shadow-sm relative overflow-hidden group hover:scale-[1.02] transition-transform cursor-pointer hover:border-amber-500/50"
                                >
                                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                        <Zap className="w-16 h-16" />
                                    </div>
                                    <p className="text-xs text-amber-600 uppercase font-bold tracking-wider mb-2 flex items-center gap-1">
                                        <Zap className="w-3 h-3" /> Top Power
                                    </p>
                                    <p className="text-lg font-bold truncate">{stats.topPowerPaddle.name}</p>
                                    <p className="text-[10px] text-muted-foreground mt-1">{stats.topPowerPaddle.powerOriginal?.toFixed(1)} Power</p>
                                </motion.div>
                            )}
                        </motion.div>

                        {/* Market Insight Card */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                            className="bg-gradient-to-r from-primary/5 to-primary/10 border border-primary/20 p-6 rounded-3xl"
                        >
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-primary/10 rounded-xl">
                                    <Award className="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <p className="text-xs text-primary uppercase font-bold tracking-wider mb-2">Insight do Mercado</p>
                                    <p className="text-lg font-bold leading-tight">
                                        {stats.mostCommonCore ? (
                                            <>
                                                <span className="text-primary">{stats.corePercentage}%</span> das raquetes usam núcleo de <span className="text-primary">{stats.mostCommonCore}</span>.
                                                {stats.mostCommonCore === '16mm' && ' Indicativo de mercado focado em controle.'}
                                                {stats.mostCommonCore === '14mm' && ' Indicativo de mercado focado em potência.'}
                                            </>
                                        ) : (
                                            <>
                                                Análise técnica revela <span className="text-primary">diversidade de núcleos</span>.
                                                Destaque para equilíbrio entre <span className="text-primary">Controle</span> e <span className="text-primary">Potência</span>.
                                            </>
                                        )}
                                    </p>
                                </div>
                            </div>
                        </motion.div>

                        {/* Hidden Gems */}
                        <HiddenGems paddles={initialPaddles} onPaddleClick={setSelectedPaddle} idealPoint={idealPoint} />

                        {/* Market Segments */}
                        <MarketSegments paddles={initialPaddles} />

                        {/* Technical Deep Dive */}
                        <TechnicalSpecsCharts paddles={initialPaddles} />

                        {/* Market Distribution */}
                        <section className="space-y-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-slate-500/10 rounded-xl">
                                    <BarChart3 className="w-6 h-6 text-slate-500" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold tracking-tight">Panorama do Mercado</h2>
                                    <p className="text-xs text-muted-foreground">Como as raquetes se distribuem.</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-[200px]">
                                <DistributionChart data={stats.distributions.prices} title="Distribuição de Preço" unit="R$" color="#10b981" binCount={8} />
                                <DistributionChart data={stats.distributions.swingWeights} title="Swing Weight" unit="" color="#8b5cf6" binCount={10} domain={[100, 130]} />
                                <DistributionChart data={stats.distributions.twistWeights} title="Twist Weight" unit="" color="#ec4899" binCount={10} domain={[4, 8]} />
                            </div>
                        </section>
                    </TabsContent>

                    {/* COMPARATIVOS TAB */}
                    <TabsContent value="comparativos" className="mt-8 space-y-12">
                        {/* Scatter Filters */}
                        <ScatterFiltersToolbar
                            brands={stats.brands}
                            priceRange={[stats.minPrice, stats.maxPrice]}
                            filters={scatterFilters}
                            onFiltersChange={setScatterFilters}
                            activeCount={filteredPaddles.length}
                            totalCount={initialPaddles.length}
                        />

                        {/* Chart 1: Price vs Performance */}
                        <section className="space-y-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-green-500/10 rounded-xl">
                                    <TrendingUp className="w-6 h-6 text-green-500" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold tracking-tight">Custo x Benefício</h2>
                                    <p className="text-xs text-muted-foreground">
                                        Encontre raquetes que entregam <strong>Alta Performance (Eixo Y)</strong> por um <strong>Preço Justo (Eixo X)</strong>.
                                        <br />
                                        <span className="text-green-600 font-bold">Dica:</span> Procure pontos no canto <strong>superior esquerdo</strong> (Alta Nota, Baixo Preço).
                                    </p>
                                </div>
                            </div>
                            <div className="h-[350px] w-full bg-card/40 backdrop-blur-sm rounded-[2rem] border border-border/50 p-4 shadow-inner relative">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} />
                                        <XAxis
                                            type="number"
                                            dataKey="priceJitter"
                                            name="Preço"
                                            unit="R$"
                                            tick={{ fontSize: 10, fill: '#888' }}
                                            tickFormatter={(val) => `R$${val / 1000}k`}
                                            domain={['dataMin - 100', 'dataMax + 100']}
                                        />
                                        <YAxis
                                            type="number"
                                            dataKey="rating"
                                            name="Rating"
                                            domain={[0, 10]}
                                            hide
                                        />
                                        <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                                        <ReferenceLine y={9.0} stroke="#10b981" strokeDasharray="3 3" label={{ value: "Elite Tier (9.0+)", position: "insideTopLeft", fill: "#10b981", fontSize: 10, fontWeight: 700 }} />
                                        <ReferenceLine x={stats.avgPrice} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "Preço Médio", position: "insideTopRight", fill: "#f59e0b", fontSize: 10, fontWeight: 700, angle: -90, dx: 10 }} />
                                        <Scatter
                                            name="Paddles"
                                            data={stats.pricePerformanceData.filter(p => filteredPaddles.some(f => f.id === p.id))}
                                            onClick={(data) => setSelectedPaddle(data.payload)}
                                            className="cursor-pointer"
                                        >
                                            {stats.pricePerformanceData.filter(p => filteredPaddles.some(f => f.id === p.id)).map((entry, index) => (
                                                <Cell
                                                    key={`cell-${index}`}
                                                    fill={entry.rating >= 9.0 ? '#10b981' : (entry.price < stats.avgPrice && entry.rating >= 8.0 ? '#f59e0b' : '#6366f1')}
                                                    fillOpacity={0.7}
                                                    stroke="none"
                                                />
                                            ))}
                                        </Scatter>
                                        {idealPoint && (
                                            <Scatter
                                                name="Seu Perfil"
                                                data={[{ priceJitter: idealPoint.price, rating: idealPoint.rating, name: 'Seu Perfil Ideal' }]}
                                                shape={(props: any) => {
                                                    const { cx, cy } = props;
                                                    return (
                                                        <g transform={`translate(${cx - 12},${cy - 12})`}>
                                                            <Star className="w-6 h-6 text-primary fill-primary shadow-glow animate-pulse" />
                                                        </g>
                                                    );
                                                }}
                                            />
                                        )}
                                    </ScatterChart>
                                </ResponsiveContainer>
                            </div>
                        </section>

                        {/* Chart 2: Power vs Control */}
                        <section className="space-y-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-blue-500/10 rounded-xl">
                                    <Scale className="w-6 h-6 text-blue-500" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold tracking-tight">
                                        <InfoTooltip term="power">Power</InfoTooltip> vs <InfoTooltip term="control">Control</InfoTooltip>
                                    </h2>
                                    <p className="text-xs text-muted-foreground">O eterno dilema. Raquetes no topo direito oferecem o melhor dos dois mundos.</p>
                                </div>
                            </div>
                            <div className="h-[350px] w-full bg-card/40 backdrop-blur-sm rounded-[2rem] border border-border/50 p-4 shadow-inner">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                                        <XAxis
                                            type="number"
                                            dataKey="x"
                                            name="Power"
                                            domain={[0, 10]}
                                            tick={{ fontSize: 10, fill: '#888' }}
                                            label={{ value: 'Power', position: 'insideBottom', offset: -5, fontSize: 10, fill: '#666', fontWeight: 700 }}
                                        />
                                        <YAxis
                                            type="number"
                                            dataKey="y"
                                            name="Control"
                                            domain={[0, 10]}
                                            tick={{ fontSize: 10, fill: '#888' }}
                                            label={{ value: 'Control', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10, fill: '#666', fontWeight: 700 }}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Scatter
                                            data={stats.powerControlData.filter(p => filteredPaddles.some(f => f.id === p.id))}
                                            fill="#3b82f6"
                                            onClick={(data) => setSelectedPaddle(data.payload)}
                                            className="cursor-pointer"
                                        >
                                            {stats.powerControlData.filter(p => filteredPaddles.some(f => f.id === p.id)).map((entry, index) => (
                                                <Cell
                                                    key={`cell-pc-${index}`}
                                                    fill={entry.x > 8 ? '#ef4444' : (entry.y > 8 ? '#3b82f6' : '#8b5cf6')}
                                                    fillOpacity={0.6}
                                                />
                                            ))}
                                        </Scatter>
                                        {idealPoint && (
                                            <Scatter
                                                name="Seu Perfil"
                                                data={[{ x: idealPoint.power, y: idealPoint.control }]}
                                                shape={(props: any) => {
                                                    const { cx, cy } = props;
                                                    return (
                                                        <g transform={`translate(${cx - 12},${cy - 12})`}>
                                                            <Star className="w-6 h-6 text-primary fill-primary shadow-glow animate-pulse" />
                                                        </g>
                                                    );
                                                }}
                                            />
                                        )}
                                    </ScatterChart>
                                </ResponsiveContainer>
                            </div>
                        </section>

                        {/* Chart 3 & 4 (Physics & Sweet Spot) */}
                        <div className="grid md:grid-cols-2 gap-8">
                            {stats.physicsData.length > 0 && (
                                <section className="space-y-6">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-purple-500/10 rounded-xl">
                                            <Activity className="w-6 h-6 text-purple-500" />
                                        </div>
                                        <div>
                                            <h2 className="text-xl font-bold tracking-tight">Physics Lab</h2>
                                            <p className="text-xs text-muted-foreground">
                                                <InfoTooltip term="twist_weight"><strong>Twist Weight (Eixo X)</strong></InfoTooltip>: Estabilidade em batidas fora do centro.<br />
                                                <InfoTooltip term="swing_weight"><strong>Swing Weight (Eixo Y)</strong></InfoTooltip>: Sensação de peso ao mover a raquete.
                                            </p>
                                        </div>
                                    </div>
                                    <div className="h-[300px] w-full bg-card/40 backdrop-blur-sm rounded-[2rem] border border-border/50 p-4 shadow-inner">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                                                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                                                <XAxis
                                                    type="number"
                                                    dataKey="x"
                                                    name="Twist Weight"
                                                    domain={['auto', 'auto']}
                                                    tick={{ fontSize: 10, fill: '#888' }}
                                                    label={{ value: 'Twist W.', position: 'insideBottom', offset: -5, fontSize: 10, fill: '#666' }}
                                                />
                                                <YAxis
                                                    type="number"
                                                    dataKey="y"
                                                    name="Swing Weight"
                                                    domain={['auto', 'auto']}
                                                    tick={{ fontSize: 10, fill: '#888' }}
                                                    label={{ value: 'Swing W.', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10, fill: '#666' }}
                                                />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Scatter
                                                    data={stats.physicsData.filter(p => filteredPaddles.some(f => f.id === p.id))}
                                                    onClick={(data) => setSelectedPaddle(data.payload)}
                                                    className="cursor-pointer"
                                                >
                                                    {stats.physicsData.filter(p => filteredPaddles.some(f => f.id === p.id)).map((entry, index) => (
                                                        <Cell key={`cell-phy-${index}`} fill={`hsl(270, 70%, ${50 + (index % 20)}%)`} fillOpacity={0.8} />
                                                    ))}
                                                </Scatter>
                                            </ScatterChart>
                                        </ResponsiveContainer>
                                    </div>
                                </section>
                            )}

                            <section className="space-y-6">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-pink-500/10 rounded-xl">
                                        <Target className="w-6 h-6 text-pink-500" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold tracking-tight">
                                            <InfoTooltip term="spin_rpm">Spin</InfoTooltip> & <InfoTooltip term="sweet_spot">Sweet Spot</InfoTooltip>
                                        </h2>
                                        <p className="text-xs text-muted-foreground">
                                            A relação entre capacidade de gerar efeito <strong>(Spin)</strong> e o tamanho da área ideal de batida <strong>(Sweet Spot)</strong>.
                                        </p>
                                    </div>
                                </div>
                                <div className="h-[300px] w-full bg-card/40 backdrop-blur-sm rounded-[2rem] border border-border/50 p-4 shadow-inner">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                                            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                                            <XAxis
                                                type="number"
                                                dataKey="x"
                                                name="Spin"
                                                domain={[0, 10]}
                                                tick={{ fontSize: 10, fill: '#888' }}
                                                label={{ value: 'Spin', position: 'insideBottom', offset: -5, fontSize: 10, fill: '#666' }}
                                            />
                                            <YAxis
                                                type="number"
                                                dataKey="y"
                                                name="Sweet Spot"
                                                domain={[0, 10]}
                                                tick={{ fontSize: 10, fill: '#888' }}
                                                label={{ value: 'Sweet Spot', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10, fill: '#666' }}
                                            />
                                            <Tooltip content={<CustomTooltip />} />
                                            <Scatter
                                                data={stats.spinSweetSpotData.filter(p => filteredPaddles.some(f => f.id === p.id))}
                                                fill="#ec4899"
                                                onClick={(data) => setSelectedPaddle(data.payload)}
                                                className="cursor-pointer"
                                            >
                                                {stats.spinSweetSpotData.filter(p => filteredPaddles.some(f => f.id === p.id)).map((entry, index) => (
                                                    <Cell key={`cell-ss-${index}`} fillOpacity={0.6} fill="#ec4899" />
                                                ))}
                                            </Scatter>
                                            {idealPoint && (
                                                <Scatter
                                                    name="Seu Perfil"
                                                    data={[{ x: idealPoint.spin, y: idealPoint.sweetSpot }]}
                                                    shape={(props: any) => {
                                                        const { cx, cy } = props;
                                                        return (
                                                            <g transform={`translate(${cx - 12},${cy - 12})`}>
                                                                <Star className="w-6 h-6 text-primary fill-primary shadow-glow animate-pulse" />
                                                            </g>
                                                        );
                                                    }}
                                                />
                                            )}
                                        </ScatterChart>
                                    </ResponsiveContainer>
                                </div>
                            </section>
                        </div>
                    </TabsContent>

                    {/* RANKINGS TAB */}
                    <TabsContent value="rankings" className="mt-8 space-y-8">
                        <section className="space-y-8">
                            <div className="flex items-center gap-3 justify-center mb-8">
                                <div className="p-3 bg-yellow-500/10 rounded-full">
                                    <Trophy className="w-8 h-8 text-yellow-500" />
                                </div>
                                <div className="text-center">
                                    <h2 className="text-3xl font-black tracking-tighter uppercase italic">Hall of Fame</h2>
                                    <p className="text-sm text-muted-foreground">Os líderes absolutos em cada categoria.</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <LeaderboardCard
                                    title="Power"
                                    subtitle="Velocidade de bola explosiva para finalizar pontos."
                                    icon={Zap}
                                    data={stats.leaderboards.topPower}
                                    colorClass="text-amber-600 bg-yellow-500/10"
                                    onPaddleClick={setSelectedPaddle}
                                />
                                <LeaderboardCard
                                    title="Spin"
                                    subtitle="Máxima rotação para controle, drops e drives curvos."
                                    icon={Wind}
                                    data={stats.leaderboards.topSpin}
                                    colorClass="text-blue-500 bg-blue-500/10"
                                    onPaddleClick={setSelectedPaddle}
                                />
                                <LeaderboardCard
                                    title="Swing Weight"
                                    subtitle="Sensação de peso maior. Mais potência, menos agilidade."
                                    icon={Activity}
                                    data={stats.leaderboards.topSwingWeight}
                                    colorClass="text-purple-500 bg-purple-500/10"
                                    onPaddleClick={setSelectedPaddle}
                                />
                                <LeaderboardCard
                                    title="Twist Weight"
                                    subtitle="Estabilidade lateral. O segredo para um Sweet Spot gigante."
                                    icon={Target}
                                    data={stats.leaderboards.topTwistWeight}
                                    colorClass="text-pink-500 bg-pink-500/10"
                                    onPaddleClick={setSelectedPaddle}
                                />
                            </div>
                        </section>
                    </TabsContent>

                    {/* MARCAS TAB */}
                    <TabsContent value="marcas" className="mt-8 space-y-8">
                        <BrandIntelligence
                            paddles={initialPaddles}
                            onBrandClick={(brand) => {
                                setScatterFilters(f => ({ ...f, brand }));
                                setActiveTab('comparativos');
                            }}
                        />
                    </TabsContent>
                </Tabs>
            </div>

            {/* Drawer for Details */}
            <Drawer open={!!selectedPaddle} onOpenChange={(open) => !open && setSelectedPaddle(null)}>
                <DrawerContent className="max-h-[85vh]">
                    {selectedPaddle && (
                        <div className="p-4 overflow-y-auto w-full max-w-2xl mx-auto">
                            <DrawerHeader className="text-left px-0 pt-0">
                                <DrawerTitle>{selectedPaddle.name}</DrawerTitle>
                                <DrawerDescription>{selectedPaddle.brand} • {selectedPaddle.weight}</DrawerDescription>
                            </DrawerHeader>
                            <div className="py-4">
                                {matchScore !== null && (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="mb-4 p-4 bg-primary/10 border border-primary/20 rounded-2xl flex items-center justify-between"
                                    >
                                        <div>
                                            <p className="text-[10px] text-primary uppercase font-black tracking-widest">Seu Match Score</p>
                                            <p className="text-3xl font-black text-primary">{matchScore}%</p>
                                        </div>
                                        <div className="text-right">
                                            <Badge className="bg-primary text-primary-foreground mb-1">
                                                {matchScore > 90 ? 'Perfect Match' : matchScore > 75 ? 'Ótima Escolha' : 'Boa Opção'}
                                            </Badge>
                                            <p className="text-[10px] text-muted-foreground whitespace-nowrap">Baseado no seu perfil</p>
                                        </div>
                                    </motion.div>
                                )}
                                <PaddleCard paddle={selectedPaddle} onClick={() => { }} />
                                {/* Additional detailed stats in drawer */}
                                <div className="mt-4 p-4 bg-muted/30 rounded-xl space-y-3">
                                    <h4 className="font-bold text-sm mb-2 flex items-center gap-2"><Activity className="w-4 h-4" /> Technical Specs</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        {selectedPaddle.swingWeight && (
                                            <div className="bg-background p-3 rounded-lg shadow-sm border border-border/50">
                                                <div className="text-[10px] text-muted-foreground uppercase font-bold flex items-center gap-1">
                                                    Swing Weight <QuickInfo term="swing_weight" />
                                                </div>
                                                <div className="font-mono text-xl">{selectedPaddle.swingWeight}</div>
                                            </div>
                                        )}
                                        {selectedPaddle.twistWeight && (
                                            <div className="bg-background p-3 rounded-lg shadow-sm border border-border/50">
                                                <div className="text-[10px] text-muted-foreground uppercase font-bold flex items-center gap-1">
                                                    Twist Weight <QuickInfo term="twist_weight" />
                                                </div>
                                                <div className="font-mono text-xl">{selectedPaddle.twistWeight}</div>
                                            </div>
                                        )}
                                        {selectedPaddle.spinRPM && (
                                            <div className="bg-background p-3 rounded-lg shadow-sm border border-border/50">
                                                <div className="text-[10px] text-muted-foreground uppercase font-bold flex items-center gap-1">
                                                    Spin RPM <QuickInfo term="spin_rpm" />
                                                </div>
                                                <div className="font-mono text-xl">{selectedPaddle.spinRPM}</div>
                                            </div>
                                        )}
                                        {selectedPaddle.powerOriginal && (
                                            <div className="bg-background p-3 rounded-lg shadow-sm border border-border/50">
                                                <div className="text-[10px] text-muted-foreground uppercase font-bold flex items-center gap-1">
                                                    Raw Power <QuickInfo term="power" />
                                                </div>
                                                <div className="font-mono text-xl">{selectedPaddle.powerOriginal}</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <DrawerFooter className="px-0">
                                <Button onClick={() => setSelectedPaddle(null)} variant="outline" className="w-full rounded-xl h-12">Fechar</Button>
                            </DrawerFooter>
                        </div>
                    )}
                </DrawerContent>
            </Drawer>

        </div>
    );
}
