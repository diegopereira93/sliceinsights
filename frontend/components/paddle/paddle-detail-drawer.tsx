import { useState, useEffect } from 'react';
import Image from 'next/image';
import { Paddle } from '@/types/paddle';
import {
    Drawer,
    DrawerClose,
    DrawerContent,
    DrawerDescription,
    DrawerFooter,
    DrawerHeader,
    DrawerTitle,
} from '@/components/ui/drawer';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Star, Zap, Weight, ShoppingCart, X, Crosshair, Tornado, Target, Layers, Ruler, Activity, ExternalLink, Globe, TrendingDown } from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { SpecItem } from '@/components/ui/spec-item';
import { PerformanceBar } from '@/components/ui/performance-bar';
import { WeightSensationScale } from '@/components/ui/weight-sensation-scale';
import { PriceSparkline } from '@/components/ui/price-sparkline';
import { CircularProgress } from '@/components/ui/circular-progress';
import { getPaddleById, getPaddlePriceHistory } from '@/lib/api';
import { ImportCalculator } from '@/components/import-calculator';
import { PriceAlertDialog } from '@/components/paddle/price-alert-dialog';
import { PriceHistoryChart } from './price-history-chart';

interface PaddleDetailDrawerProps {
    paddle: Paddle | null;
    isOpen: boolean;
    onClose: () => void;
}

interface MarketOffer {
    store_name: string;
    price_brl: number;
    url: string;
    affiliate_url?: string;
    last_updated: string;
}

interface PaddleDetails extends Paddle {
    market_offers?: MarketOffer[];
}

export function PaddleDetailDrawer({ paddle: initialPaddle, isOpen, onClose }: PaddleDetailDrawerProps) {
    const [details, setDetails] = useState<PaddleDetails | null>(null);
    const [loading, setLoading] = useState(false);
    const [priceHistory, setPriceHistory] = useState<any>(null);

    useEffect(() => {
        if (isOpen && initialPaddle) {
            setDetails(initialPaddle as PaddleDetails);
            setLoading(true);

            // Parallel fetches
            Promise.all([
                getPaddleById(initialPaddle.id),
                getPaddlePriceHistory(initialPaddle.id)
            ])
                .then(([data, historyData]) => {
                    setDetails(prev => ({
                        ...prev!,
                        market_offers: data.market_offers,
                        availableInBrazil: data.available_in_brazil,
                    }));
                    setPriceHistory(historyData.history);
                })
                .catch(err => console.error("Error fetching paddle details/history:", err))
                .finally(() => setLoading(false));
        } else {
            setDetails(null);
            setPriceHistory(null);
        }
    }, [isOpen, initialPaddle]);

    if (!initialPaddle) return null;
    const displayPaddle = details || initialPaddle;

    // Get the best offer (cheapest)
    const offers = (displayPaddle as PaddleDetails).market_offers;
    const bestOffer = offers?.length
        ? [...offers].sort((a, b) => a.price_brl - b.price_brl)[0]
        : null;

    const buyUrl = bestOffer?.affiliate_url || bestOffer?.url || "#";

    return (
        <Drawer open={isOpen} onOpenChange={onClose}>
            <DrawerContent className="max-h-[96vh] glass-dark border-none">
                <div className="mx-auto w-12 h-1.5 flex-shrink-0 rounded-full bg-muted mb-4 mt-2" />

                <DrawerHeader className="relative pb-0">
                    <DrawerClose asChild className="absolute right-4 top-0 z-10">
                        <Button variant="ghost" size="icon" className="rounded-full bg-muted/50">
                            <X className="w-5 h-5" />
                        </Button>
                    </DrawerClose>
                    <div className="flex flex-col gap-1 items-start">
                        <Badge variant="outline" className="text-secondary-foreground border-border font-bold uppercase tracking-widest text-[10px]">
                            {displayPaddle.brand}
                        </Badge>
                        <DrawerTitle className="text-2xl font-black text-left">{displayPaddle.name}</DrawerTitle>
                        <div className="flex items-center gap-2 mt-1">
                            <div className="flex items-center text-yellow-500">
                                <Star className="w-4 h-4 fill-current" />
                                <span className="ml-1 text-sm font-bold">{displayPaddle.rating.toFixed(1)}</span>
                            </div>
                            <Separator orientation="vertical" className="h-4" />
                            <span className="text-sm text-muted-foreground font-medium">Top Rated</span>
                        </div>
                    </div>
                </DrawerHeader>

                <div className="px-4 py-6 overflow-y-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="relative aspect-square rounded-3xl overflow-hidden bg-secondary/20 group">
                            <Image
                                src={displayPaddle.image}
                                alt={displayPaddle.name}
                                fill
                                className="object-cover transition-transform duration-700 group-hover:scale-110"
                            />
                            <div className="absolute bottom-4 left-4 right-4 flex flex-wrap gap-2">
                                <Badge className="bg-primary/90 backdrop-blur-md text-primary-foreground border-none px-3 py-1 font-bold">
                                    {displayPaddle.powerLevel} Power
                                </Badge>
                                <Badge className="bg-blue-500/90 backdrop-blur-md text-white border-none px-3 py-1 font-bold">
                                    {displayPaddle.controlLevel} Control
                                </Badge>
                                {displayPaddle.availableInBrazil === false && (
                                    <Badge className="bg-amber-500/90 backdrop-blur-md text-amber-950 border-none px-3 py-1 font-bold flex items-center gap-1">
                                        <Globe className="w-3 h-3" /> IMPORTADO
                                    </Badge>
                                )}
                                {displayPaddle.tags?.map((tag, i) => (
                                    <Badge key={i} className="bg-black/80 backdrop-blur-md text-white border-none px-3 py-1 font-bold">
                                        {tag}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-6">
                            {displayPaddle.matchReasons && displayPaddle.matchReasons.length > 0 && (
                                <div className="bg-primary/5 p-4 rounded-2xl border border-primary/10">
                                    <h4 className="text-xs font-black uppercase tracking-widest text-primary-text mb-3">Por que esta raquete?</h4>
                                    <ul className="space-y-2">
                                        {displayPaddle.matchReasons.map((reason, i) => (
                                            <li key={i} className="text-sm flex items-start gap-2 font-medium">
                                                <Zap className="w-4 h-4 text-primary-text shrink-0 mt-0.5" />
                                                {reason}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Data Transparency Section */}
                            {displayPaddle.isSynthetic && (
                                <div className="bg-amber-500/15 dark:bg-amber-500/10 p-4 rounded-2xl border border-amber-500/20">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Badge variant="outline" className="border-amber-600 text-amber-700 dark:border-amber-500 dark:text-amber-400 font-bold uppercase text-[10px]">
                                            Dados Estimados
                                        </Badge>
                                    </div>
                                    <p className="text-xs text-amber-900 dark:text-amber-100 font-medium leading-relaxed">
                                        As especificações desta raquete foram estimadas pelo nosso algoritmo com base nas características do modelo e dados parciais, pois o fabricante não forneceu métricas oficiais completas.
                                    </p>
                                </div>
                            )}

                            {displayPaddle.swingWeight && (
                                <WeightSensationScale swingWeight={displayPaddle.swingWeight} />
                            )}

                            {/* Price History Chart Section */}
                            <div className="bg-zinc-900/40 p-5 rounded-2xl border border-white/5">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                                        <TrendingDown className="w-4 h-4 text-primary-text" /> Histórico de Preços
                                    </h4>
                                    <Badge variant="secondary" className="text-[9px] h-5 bg-white/5 border-none text-zinc-400">Últimos 30 dias</Badge>
                                </div>
                                {loading && !priceHistory ? (
                                    <div className="h-48 animate-pulse bg-white/5 rounded-xl" />
                                ) : (
                                    <PriceHistoryChart history={priceHistory || {}} />
                                )}
                            </div>

                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4">Especificações Técnicas</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <SpecItem icon={Weight} label="Peso Médio" value={displayPaddle.weight || 'N/A'} />
                                    <SpecItem icon={Layers} label="Face" value={displayPaddle.faceMaterial || displayPaddle.surfaceMaterial || 'N/A'} />
                                    <SpecItem icon={Layers} label="Core" value={displayPaddle.coreMaterial || 'Polymer'} />
                                    {displayPaddle.gripCircumference && (
                                        <SpecItem icon={Ruler} label="Grip" value={displayPaddle.gripCircumference} />
                                    )}
                                    {displayPaddle.swingWeight && (
                                        <SpecItem icon={Activity} label="Swing Weight" value={displayPaddle.swingWeight.toString()} />
                                    )}
                                    {displayPaddle.twistWeight && (
                                        <SpecItem icon={Tornado} label="Twist Weight" value={displayPaddle.twistWeight.toString()} />
                                    )}
                                    {displayPaddle.handleLength && (
                                        <SpecItem icon={Ruler} label="Cabo" value={`${displayPaddle.handleLength}"`} />
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-wrap items-center justify-center gap-4 py-2">
                                <CircularProgress
                                    value={displayPaddle.powerLevel === 'High' ? 90 : displayPaddle.powerLevel === 'Medium' ? 60 : 40}
                                    label="Potência"
                                    icon={Zap}
                                    colorClass="text-primary-text"
                                    strokeColor="#CEFF00"
                                />
                                <CircularProgress
                                    value={displayPaddle.controlLevel === 'High' ? 90 : displayPaddle.controlLevel === 'Medium' ? 60 : 40}
                                    label="Controle"
                                    icon={Crosshair}
                                    colorClass="text-blue-400"
                                    strokeColor="#60A5FA"
                                />
                                <CircularProgress
                                    value={displayPaddle.spinRPM ? (displayPaddle.spinRPM / 250 * 100) : (displayPaddle.spin || 5) * 10}
                                    label={`Spin ${displayPaddle.spinRPM ? `(${displayPaddle.spinRPM})` : ''}`}
                                    icon={Tornado}
                                    colorClass="text-purple-400"
                                    strokeColor="#C084FC"
                                />
                                <CircularProgress
                                    value={(displayPaddle.sweetSpot || 7) * 10}
                                    label="Sweet Spot"
                                    icon={Target}
                                    colorClass="text-green-400"
                                    strokeColor="#4ADE80"
                                />
                            </div>

                            <div className="pt-4">
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    A raquete <span className="text-foreground font-bold">{displayPaddle.name}</span> da <span className="text-foreground font-bold">{displayPaddle.brand}</span> foi projetada para jogadores que buscam {displayPaddle.powerLevel === 'High' ? 'explosividade e força nos golpes' : 'máxima precisão e toque suave'}. {displayPaddle.surfaceMaterial ? `Seu acabamento em ${displayPaddle.surfaceMaterial} garante durabilidade superior e spin consistente.` : ''}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <DrawerFooter className="border-t border-border/50 bg-background/50 backdrop-blur-md pt-6 pb-24 md:pb-10 px-4 sm:px-6">
                    <div className="flex items-center justify-between gap-4 max-w-4xl mx-auto w-full">
                        <div className="flex flex-col">
                            <span className="text-xs text-muted-foreground font-medium uppercase tracking-tighter">Preço Especial</span>
                            <span className="text-3xl font-black text-primary-text tracking-tighter">
                                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(displayPaddle.price)}
                            </span>
                        </div>
                        <div className="flex-1 max-w-[120px] hidden sm:block">
                            <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest block mb-1">Últimos 7 dias</span>
                            <PriceSparkline paddleId={displayPaddle.id} currentPrice={displayPaddle.price} />
                        </div>
                        <div className="flex items-center gap-2">
                            {displayPaddle.availableInBrazil === false && (
                                <ImportCalculator
                                    initialPrice={displayPaddle.price / 5.0} // Estimated USD
                                    localPriceBRL={displayPaddle.price}
                                    paddleWeight={350}
                                    variant="outline"
                                    size="lg"
                                />
                            )}
                            <PriceAlertDialog
                                paddleId={displayPaddle.id}
                                currentPrice={displayPaddle.price}
                            />
                            <Button
                                size="lg"
                                className="h-14 px-8 rounded-2xl bg-primary text-primary-foreground font-black text-lg shadow-lg shadow-primary/20 group"
                                onClick={() => window.open(buyUrl, '_blank')}
                                disabled={buyUrl === "#"}
                            >
                                {displayPaddle.availableInBrazil === false ? "VER INTERNACIONAL" : "COMPRAR AGORA"}
                                <ShoppingCart className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" />
                            </Button>
                        </div>
                    </div>
                </DrawerFooter>
            </DrawerContent>
        </Drawer>
    );
}
