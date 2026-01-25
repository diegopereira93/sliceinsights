'use client';

import { Paddle } from '@/components/paddle/paddle-card';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Zap, Shield, Weight, Activity, Ruler, Layers, Target, Tornado, X, ShoppingCart } from 'lucide-react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { WeightSensationScale } from '../ui/weight-sensation-scale';

interface PaddleComparatorProps {
    paddles: Paddle[] | null;
    isOpen: boolean;
    onClose: () => void;
}

export function PaddleComparator({ paddles, isOpen, onClose }: PaddleComparatorProps) {
    if (!paddles || paddles.length < 2) return null;

    const p1 = paddles[0];
    const p2 = paddles[1];

    const SpecRow = ({ icon: Icon, label, v1, v2, higherIsBetter = true }: { icon: any, label: string, v1: any, v2: any, higherIsBetter?: boolean }) => {
        const isV1Better = typeof v1 === 'number' && typeof v2 === 'number' ? (higherIsBetter ? v1 > v2 : v1 < v2) : false;
        const isV2Better = typeof v1 === 'number' && typeof v2 === 'number' ? (higherIsBetter ? v2 > v1 : v2 < v1) : false;

        return (
            <div className="py-4 border-b border-white/5">
                <div className="flex items-center gap-2 mb-3 justify-center">
                    <Icon className="w-4 h-4 text-muted-foreground" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{label}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div className={`text-center p-3 rounded-xl transition-colors ${isV1Better ? 'bg-primary/10 border border-primary/20' : 'bg-white/5'}`}>
                        <span className={`text-sm font-bold ${isV1Better ? 'text-primary-text' : ''}`}>{v1 || '-'}</span>
                    </div>
                    <div className={`text-center p-3 rounded-xl transition-colors ${isV2Better ? 'bg-primary/10 border border-primary/20' : 'bg-white/5'}`}>
                        <span className={`text-sm font-bold ${isV2Better ? 'text-primary-text' : ''}`}>{v2 || '-'}</span>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent side="bottom" className="h-[90vh] glass-dark border-none rounded-t-[3rem] p-0 overflow-hidden">
                <SheetHeader className="p-6 pb-2 border-b border-white/10 flex flex-row items-center justify-between">
                    <SheetTitle className="text-xl font-black italic uppercase tracking-tighter">BATTLE MODE</SheetTitle>
                    <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full bg-white/5 hover:bg-white/10">
                        <X className="w-5 h-5" />
                    </Button>
                </SheetHeader>

                <div className="h-full overflow-y-auto pb-20">
                    <div className="px-6 py-8">
                        {/* Header Paddles */}
                        <div className="grid grid-cols-2 gap-8 mb-12">
                            {[p1, p2].map((p, i) => (
                                <div key={i} className="flex flex-col items-center text-center gap-4">
                                    <div className="relative w-full aspect-square rounded-3xl overflow-hidden bg-secondary/20 shadow-2xl">
                                        <Image src={p.image} alt={p.name} fill className="object-cover" />
                                        <div className="absolute top-2 left-2">
                                            <Badge variant="secondary" className="bg-black/60 text-white border-none text-[10px] font-bold">
                                                {p.brand}
                                            </Badge>
                                        </div>
                                    </div>
                                    <h3 className="text-sm font-black leading-tight h-10 flex items-center">{p.name}</h3>
                                    <div className="flex flex-col">
                                        <span className="text-xl font-black text-primary-text">
                                            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(p.price)}
                                        </span>
                                    </div>
                                    <Button size="sm" className="w-full bg-primary text-primary-foreground font-bold rounded-xl h-10 group">
                                        SHOP
                                        <ShoppingCart className="ml-2 w-4 h-4 transition-transform group-hover:translate-x-1" />
                                    </Button>
                                </div>
                            ))}
                        </div>

                        {/* Specs Comparison */}
                        <div className="space-y-2">
                            <SpecRow icon={Zap} label="Power Rating" v1={p1.power} v2={p2.power} />
                            <SpecRow icon={Shield} label="Control Rating" v1={p1.control} v2={p2.control} />
                            <SpecRow icon={Tornado} label="Spin" v1={p1.spin} v2={p2.spin} />
                            <SpecRow icon={Target} label="Sweet Spot" v1={p1.sweetSpot} v2={p2.sweetSpot} />
                            <SpecRow icon={Activity} label="Swing Weight" v1={p1.swingWeight} v2={p2.swingWeight} higherIsBetter={false} />
                            <SpecRow icon={Ruler} label="Core Thickness" v1={p1.coreThicknessmm} v2={p2.coreThicknessmm} />

                            <div className="py-6">
                                <div className="flex items-center gap-2 mb-4 justify-center">
                                    <Weight className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Sensation</span>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex flex-col gap-2">
                                        <WeightSensationScale swingWeight={p1.swingWeight || 0} />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <WeightSensationScale swingWeight={p2.swingWeight || 0} />
                                    </div>
                                </div>
                            </div>

                            <SpecRow icon={Layers} label="Surface" v1={p1.surfaceMaterial} v2={p2.surfaceMaterial} />
                            <SpecRow icon={Ruler} label="Handle" v1={p1.handleLength} v2={p2.handleLength} />
                        </div>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    );
}
