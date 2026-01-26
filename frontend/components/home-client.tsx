'use client';

import { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaddleCard, Paddle } from '@/components/paddle/paddle-card';
import { FilterDrawer } from '@/components/paddle/filter-drawer';
import { RacketFinderQuiz } from '@/components/paddle/racket-finder-quiz';
import { PaddleDetailDrawer } from '@/components/paddle/paddle-detail-drawer';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Sparkles, Search, X, Swords } from 'lucide-react';
import { PaddleComparator } from './paddle/paddle-comparator';
import { Button } from '@/components/ui/button';

interface HomeClientProps {
    initialPaddles: Paddle[];
    availableBrands: string[];
}

const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
};

export function HomeClient({ initialPaddles, availableBrands }: HomeClientProps) {
    const [selectedPaddle, setSelectedPaddle] = useState<Paddle | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    // Filter States
    const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
    const [priceRange, setPriceRange] = useState<[number, number]>([0, 10000]); // 0 to Max

    // Comparison State
    const [comparingPaddles, setComparingPaddles] = useState<Paddle[]>([]);
    const [isBattleModeOpen, setIsBattleModeOpen] = useState(false);

    // Derived state for filtering
    const filteredPaddles = useMemo(() => {
        return initialPaddles.filter(paddle => {
            // 1. Search Query
            const matchesSearch = searchQuery === '' ||
                paddle.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                paddle.brand.toLowerCase().includes(searchQuery.toLowerCase());

            // 2. Brand Filter
            const matchesBrand = selectedBrands.length === 0 || selectedBrands.includes(paddle.brand);

            // 3. Price Filter (Simple implementation for now)
            const matchesPrice = paddle.price >= priceRange[0] && paddle.price <= priceRange[1];

            return matchesSearch && matchesBrand && matchesPrice;
        });
    }, [initialPaddles, searchQuery, selectedBrands, priceRange]);

    const handleRecommend = (paddle: Paddle) => {
        setSelectedPaddle(paddle);
    };

    const handleClearFilters = () => {
        setSearchQuery('');
        setSelectedBrands([]);
        setPriceRange([0, 10000]);
    };

    const handleCompare = useCallback((paddle: Paddle) => {
        setComparingPaddles(prev => {
            const isAlreadyIn = prev.some(p => p.id === paddle.id);
            if (isAlreadyIn) {
                return prev.filter(p => p.id !== paddle.id);
            }
            if (prev.length >= 2) {
                // Keep the most recent and add the new one
                return [prev[1], paddle];
            }
            return [...prev, paddle];
        });
    }, []);

    return (
        <div className="space-y-12 pb-20">
            {/* Hero / Quiz Section */}
            <section className="relative overflow-hidden rounded-3xl bg-neutral-900 px-6 py-12 text-white dark">
                <div className="absolute top-0 right-0 -mt-10 -mr-10 h-64 w-64 rounded-full bg-primary/20 blur-3xl" />
                <div className="relative z-10 flex flex-col items-center text-center">
                    <Badge className="mb-4 bg-primary text-primary-foreground border-none font-bold tracking-widest uppercase py-1 px-3">
                        <Sparkles className="w-4 h-4 mr-2 fill-current" /> AI Advisor
                    </Badge>
                    <h1 className="mb-6 text-3xl font-black md:text-5xl lg:max-w-3xl">
                        Descubra com a <span className="text-primary italic">SliceInsights</span> a raquete perfeita para o seu jogo.
                    </h1>

                    <div className="w-full mt-4">
                        <RacketFinderQuiz paddles={initialPaddles} onRecommend={handleRecommend} />
                    </div>
                </div>
            </section>

            <section id="catalog">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                    <div>
                        <h2 className="text-2xl font-black tracking-tighter uppercase italic">
                            {searchQuery || selectedBrands.length > 0 ? 'Resultados da Busca' : 'Catálogo de Raquetes'}
                        </h2>
                        <div className="h-1.5 w-12 bg-primary rounded-full mt-1" />
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <div className="relative flex-1 md:w-64">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                placeholder="Buscar raquete..."
                                className="pl-9 bg-muted/50 border-none shadow-inner"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 hover:text-foreground text-muted-foreground"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>

                        <FilterDrawer
                            brands={availableBrands}
                            selectedBrands={selectedBrands}
                            onToggleBrand={(brand) => {
                                setSelectedBrands(prev =>
                                    prev.includes(brand) ? prev.filter(b => b !== brand) : [...prev, brand]
                                );
                            }}
                            onClear={handleClearFilters}
                        />
                    </div>
                </div>

                {filteredPaddles.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center opacity-70">
                        <Search className="w-12 h-12 mb-4 text-muted-foreground" />
                        <h3 className="text-xl font-bold">Nenhuma raquete encontrada</h3>
                        <p className="text-sm text-muted-foreground">Tente ajustar seus filtros ou busca.</p>
                        <button
                            onClick={handleClearFilters}
                            className="mt-4 text-primary font-bold hover:underline"
                        >
                            Limpar filtros
                        </button>
                    </div>
                ) : (
                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        animate="show"
                        key={searchQuery + selectedBrands.join(',')}
                        className="grid grid-cols-2 lg:grid-cols-4 gap-6"
                    >
                        {filteredPaddles.map((paddle) => (
                            <motion.div key={paddle.id} variants={itemVariants}>
                                <PaddleCard
                                    paddle={paddle}
                                    onClick={() => setSelectedPaddle(paddle)}
                                    onCompare={handleCompare}
                                    isComparing={comparingPaddles.some(p => p.id === paddle.id)}
                                />
                            </motion.div>
                        ))}
                    </motion.div>
                )}
            </section>

            <PaddleDetailDrawer
                paddle={selectedPaddle}
                isOpen={!!selectedPaddle}
                onClose={() => setSelectedPaddle(null)}
            />

            {/* Battle Mode Trigger Bar */}
            <AnimatePresence>
                {comparingPaddles.length > 0 && (
                    <motion.div
                        key="battle-bar"
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: 100, opacity: 0 }}
                        className="fixed bottom-24 left-0 right-0 z-[100] flex justify-center px-4 pointer-events-none"
                    >
                        <div className="bg-neutral-900/95 backdrop-blur-2xl border border-white/20 rounded-full px-6 py-4 flex items-center gap-6 shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-primary/20 pointer-events-auto">
                            <div className="flex -space-x-4">
                                {comparingPaddles.map((p) => (
                                    <div key={p.id} className="w-12 h-12 rounded-full border-2 border-primary overflow-hidden bg-muted shadow-lg">
                                        <img src={p.image} alt={p.name} className="w-full h-full object-cover" />
                                    </div>
                                ))}
                            </div>
                            <div className="flex flex-col min-w-[80px]">
                                <span className="text-[10px] font-black uppercase text-primary tracking-widest leading-none">Modo de Batalha</span>
                                <span className="text-sm font-bold text-white leading-none mt-1">
                                    {comparingPaddles.length} {comparingPaddles.length === 1 ? 'raquete' : 'raquetes'}
                                </span>
                            </div>
                            <Button
                                disabled={comparingPaddles.length < 2}
                                onClick={() => setIsBattleModeOpen(true)}
                                className="bg-primary text-primary-foreground font-black rounded-full px-8 h-12 shadow-[0_0_20px_rgba(206,255,0,0.4)] hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Swords className="size-5 mr-2" />
                                LUTAR!
                            </Button>
                            <button
                                onClick={() => setComparingPaddles([])}
                                className="p-2 text-white/40 hover:text-white transition-colors bg-white/5 rounded-full"
                            >
                                <X className="size-5" />
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <PaddleComparator
                paddles={comparingPaddles.length === 2 ? [comparingPaddles[0], comparingPaddles[1]] : null}
                isOpen={isBattleModeOpen}
                onClose={() => {
                    setIsBattleModeOpen(false);
                }}
            />
        </div>
    );
}
