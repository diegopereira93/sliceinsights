'use client';

import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Search, 
    Zap, 
    Trophy, 
    ChevronRight, 
    Sparkles,
    MousePointer2,
    BarChart3,
    MessageSquare,
    Ghost,
    Swords,
    X
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Paddle } from '@/types/paddle';
import { PaddleCard } from '@/components/paddle/paddle-card';
import { FilterDrawer } from '@/components/paddle/filter-drawer';
import { RacketFinderQuiz } from '@/components/paddle/racket-finder-quiz';
import { PaddleDetailDrawer } from '@/components/paddle/paddle-detail-drawer';
import { PaddleComparator } from '@/components/paddle/paddle-comparator';
import { mapBackendToFrontendPaddle } from '@/lib/api';

interface HomeClientProps {
    initialPaddles: Paddle[];
    brands: string[];
}

export default function HomeClient({ initialPaddles, brands }: HomeClientProps) {
    const [paddles, setPaddles] = useState<Paddle[]>(initialPaddles);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
    const [priceRange, setPriceRange] = useState<[number, number]>([0, 4000]);
    const [weightFilter, setWeightFilter] = useState<"all" | "light" | "standard" | "heavy">("all");
    const [thicknessFilter, setThicknessFilter] = useState<"all" | "14mm" | "16mm">("all");
    
    const [selectedPaddle, setSelectedPaddle] = useState<Paddle | null>(null);
    const [comparisonList, setComparisonList] = useState<Paddle[]>([]);
    const [isComparatorOpen, setIsComparatorOpen] = useState(false);
    const [isQuizOpen, setIsQuizOpen] = useState(false);

    // Filter logic
    const filteredPaddles = useMemo(() => {
        return paddles.filter(paddle => {
            const matchesSearch = paddle.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                                 paddle.brand.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesBrand = selectedBrands.length === 0 || selectedBrands.includes(paddle.brand);
            const matchesPrice = paddle.price >= priceRange[0] && (priceRange[1] === 4000 ? true : paddle.price <= priceRange[1]);
            
            let matchesWeight = true;
            if (weightFilter !== "all") {
                const weightNum = parseFloat(paddle.weight || "0");
                if (weightFilter === "light") matchesWeight = weightNum < 7.8;
                else if (weightFilter === "standard") matchesWeight = weightNum >= 7.8 && weightNum <= 8.2;
                else if (weightFilter === "heavy") matchesWeight = weightNum > 8.2;
            }

            let matchesThickness = true;
            if (thicknessFilter !== "all") {
                const thickness = paddle.coreThicknessmm || 0;
                if (thicknessFilter === "14mm") matchesThickness = thickness < 15;
                else if (thicknessFilter === "16mm") matchesThickness = thickness >= 15;
            }

            return matchesSearch && matchesBrand && matchesPrice && matchesWeight && matchesThickness;
        });
    }, [paddles, searchQuery, selectedBrands, priceRange, weightFilter, thicknessFilter]);

    const handleToggleBrand = (brand: string) => {
        setSelectedBrands(prev => 
            prev.includes(brand) ? prev.filter(b => b !== brand) : [...prev, brand]
        );
    };

    const handleClearFilters = () => {
        setSelectedBrands([]);
        setPriceRange([0, 4000]);
        setWeightFilter("all");
        setThicknessFilter("all");
        setSearchQuery("");
    };

    const handleCompare = (paddle: Paddle) => {
        setComparisonList(prev => {
            if (prev.find(p => p.id === paddle.id)) {
                return prev.filter(p => p.id !== paddle.id);
            }
            if (prev.length >= 2) {
                return [prev[1], paddle];
            }
            return [...prev, paddle];
        });
    };

    return (
        <div className="min-h-screen bg-background relative overflow-hidden">
            {/* Background Glows */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />

            {/* Hero Section */}
            <section className="relative pt-20 pb-16 px-6">
                <div className="max-w-7xl mx-auto text-center space-y-8">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <Badge variant="secondary" className="mb-4 px-4 py-1 rounded-full bg-white/5 border-white/10 text-primary-text font-black tracking-widest uppercase italic text-[10px]">
                            <Sparkles className="w-3 h-3 mr-2" /> Inteligência em Equipamento
                        </Badge>
                        <h1 className="text-5xl md:text-7xl font-black italic uppercase tracking-tighter leading-[0.9] mb-6">
                            Domine a Quadra com a <span className="text-primary shadow-glow">Raquete Perfeita</span>
                        </h1>
                        <p className="text-zinc-400 max-w-2xl mx-auto text-lg md:text-xl font-medium">
                            Analisamos as métricas de desempenho de centenas de raquetes para encontrar o match ideal para o seu estilo de jogo.
                        </p>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="flex flex-col sm:flex-row items-center justify-center gap-4"
                    >
                        <Button 
                            size="lg" 
                            className="h-14 px-8 rounded-2xl bg-primary text-primary-foreground font-black text-lg shadow-lg shadow-primary/20 group"
                            onClick={() => setIsQuizOpen(true)}
                        >
                            ENCONTRAR MINHA RAQUETE
                            <ChevronRight className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" />
                        </Button>
                        <Button 
                            variant="outline" 
                            size="lg" 
                            className="h-14 px-8 rounded-2xl border-white/10 bg-white/5 font-bold hover:bg-white/10"
                            onClick={() => window.scrollTo({ top: window.innerHeight * 0.8, behavior: 'smooth' })}
                        >
                            EXPLORAR CATÁLOGO
                        </Button>
                    </motion.div>
                </div>
            </section>

            {/* Catalog Toolbar */}
            <div className="sticky top-0 z-40 glass-dark border-b border-white/5 py-4 px-6 md:px-12 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="relative w-full md:w-96 group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-primary transition-colors" />
                        <Input 
                            placeholder="Buscar por modelo ou marca..." 
                            className="pl-11 bg-white/5 border-white/10 h-12 rounded-xl focus:ring-primary/20"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    
                    <div className="flex items-center gap-3 w-full md:w-auto overflow-x-auto pb-1 md:pb-0 scrollbar-none">
                        <FilterDrawer 
                            brands={brands}
                            selectedBrands={selectedBrands}
                            onToggleBrand={handleToggleBrand}
                            priceRange={priceRange}
                            onPriceRangeChange={setPriceRange}
                            weightFilter={weightFilter}
                            onWeightChange={setWeightFilter}
                            thicknessFilter={thicknessFilter}
                            onThicknessChange={setThicknessFilter}
                            onClear={handleClearFilters}
                        />



                        <Badge variant="outline" className="h-10 px-4 rounded-full border-white/5 bg-white/5 text-zinc-400 flex flex-shrink-0">
                            {filteredPaddles.length} Raquetes
                        </Badge>
                    </div>
                </div>
            </div>

            {/* Catalog Grid */}
            <main className="max-w-7xl mx-auto px-6 py-12">
                <AnimatePresence mode="popLayout">
                    {filteredPaddles.length > 0 ? (
                        <motion.div 
                            layout
                            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                        >
                            {filteredPaddles.map((paddle) => (
                                <motion.div
                                    key={paddle.id}
                                    layout
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <PaddleCard 
                                        paddle={paddle} 
                                        onClick={() => setSelectedPaddle(paddle)}
                                        onCompare={() => handleCompare(paddle)}
                                        isComparing={comparisonList.some(p => p.id === paddle.id)}
                                    />
                                </motion.div>
                            ))}
                        </motion.div>
                    ) : (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex flex-col items-center justify-center py-20 text-center"
                        >
                            <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6">
                                <Ghost className="w-10 h-10 text-zinc-600" />
                            </div>
                            <h3 className="text-xl font-bold mb-2">Nenhuma raquete encontrada</h3>
                            <p className="text-zinc-500 mb-8 max-w-sm">Tente ajustar seus filtros ou busca para encontrar o que procura.</p>
                            <Button onClick={handleClearFilters} variant="outline" className="rounded-xl">
                                Limpar Todos os Filtros
                            </Button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>

            {/* Modals & Overlays */}
            <PaddleDetailDrawer 
                paddle={selectedPaddle}
                isOpen={!!selectedPaddle}
                onClose={() => setSelectedPaddle(null)}
            />

            {/* Battle Mode Trigger Bar */}
            <AnimatePresence>
                {comparisonList.length > 0 && (
                    <motion.div
                        key="battle-bar"
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: 100, opacity: 0 }}
                        className="fixed bottom-24 left-0 right-0 z-[100] flex justify-center px-4 pointer-events-none"
                    >
                        <div className="bg-neutral-900/95 backdrop-blur-2xl border border-white/20 rounded-full px-6 py-4 flex items-center gap-6 shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-primary/20 pointer-events-auto">
                            <div className="flex -space-x-4">
                                {comparisonList.map((p) => (
                                    <div key={p.id} className="w-12 h-12 rounded-full border-2 border-primary overflow-hidden bg-muted shadow-lg">
                                        <img src={p.image || '/placeholder-paddle.png'} alt={p.name} className="w-full h-full object-cover" />
                                    </div>
                                ))}
                            </div>
                            <div className="flex flex-col min-w-[80px]">
                                <span className="text-[10px] font-black uppercase text-primary tracking-widest leading-none">Modo de Batalha</span>
                                <span className="text-sm font-bold text-white leading-none mt-1">
                                    {comparisonList.length} {comparisonList.length === 1 ? 'raquete' : 'raquetes'}
                                </span>
                            </div>
                            <Button
                                disabled={comparisonList.length < 2}
                                onClick={() => setIsComparatorOpen(true)}
                                className="bg-primary text-primary-foreground font-black rounded-full px-8 h-12 shadow-[0_0_20px_rgba(206,255,0,0.4)] hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Swords className="size-5 mr-2" />
                                LUTAR!
                            </Button>
                            <button
                                onClick={() => setComparisonList([])}
                                className="p-2 text-white/40 hover:text-white transition-colors bg-white/5 rounded-full"
                            >
                                <X className="size-5" />
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <PaddleComparator 
                paddles={comparisonList}
                isOpen={isComparatorOpen}
                onClose={() => setIsComparatorOpen(false)}
            />

            <AnimatePresence>
                {isQuizOpen && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md"
                    >
                        <motion.div 
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="w-full max-w-2xl max-h-[90vh] overflow-y-auto glass-dark p-8 rounded-[2rem] border-white/10 relative shadow-2xl"
                        >
                            <Button 
                                variant="ghost" 
                                size="icon" 
                                onClick={() => setIsQuizOpen(false)}
                                className="absolute right-6 top-6 rounded-full hover:bg-white/10"
                            >
                                <MousePointer2 className="w-5 h-5" />
                            </Button>
                            
                            <div className="mb-8 text-center">
                                <h2 className="text-3xl font-black italic uppercase tracking-tighter text-primary">Racket Finder AI</h2>
                                <p className="text-zinc-500 text-sm mt-2">Responda 10 perguntas e encontre seu match técnico.</p>
                            </div>

                            <RacketFinderQuiz 
                                paddles={paddles}
                                onRecommend={(paddle) => {
                                    setIsQuizOpen(false);
                                    setSelectedPaddle(paddle);
                                }}
                            />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Floating CTA */}
            <motion.div 
                initial={{ opacity: 0, y: 100 }}
                animate={{ opacity: 1, y: 0 }}
                className="fixed bottom-8 right-8 z-40 hidden md:block"
            >
                <Button 
                    className="h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-2xl shadow-primary/40 p-0 overflow-hidden group relative"
                    onClick={() => setIsQuizOpen(true)}
                >
                    <MessageSquare className="w-6 h-6 transition-transform group-hover:scale-110" />
                    <motion.div 
                        animate={{ scale: [1, 1.2, 1] }} 
                        transition={{ duration: 2, repeat: Infinity }}
                        className="absolute inset-0 bg-white/20 rounded-full pointer-events-none" 
                    />
                </Button>
            </motion.div>
        </div>
    );
}
