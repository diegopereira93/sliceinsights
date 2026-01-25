import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Star, Zap, Shield, Weight, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { WeightSensationScale } from '@/components/ui/weight-sensation-scale';

export interface Paddle {
    id: string;
    name: string;
    brand: string;
    price: number;
    image: string;
    rating: number; // User visual rating (e.g. 4.5)
    weight: string;
    surfaceMaterial: string;
    powerLevel: 'High' | 'Medium' | 'Low';
    controlLevel: 'High' | 'Medium' | 'Low';
    power: number;      // 0-10
    control: number;    // 0-10
    spin: number;       // 0-10
    sweetSpot: number;  // 0-10
    matchReasons?: string[];
    tags?: string[];
    availableInBrazil?: boolean;
    affiliateUrl?: string;

    // Detailed Specs
    swingWeight?: number;
    twistWeight?: number;
    spinRPM?: number;
    powerOriginal?: number;
    coreThicknessmm?: number;
    handleLength?: string;
    gripCircumference?: string;
    coreMaterial?: string;
    faceMaterial?: string; // Specific face material from spec
}

interface PaddleCardProps {
    paddle: Paddle;
    onClick?: () => void;
    onCompare?: (paddle: Paddle) => void;
    isComparing?: boolean;
}

export function PaddleCard({ paddle, onClick, onCompare, isComparing }: PaddleCardProps) {
    return (
        <motion.div
            whileHover={{ y: -8, scale: 1.02 }}
            whileTap={{ scale: 0.95 }}
            className="h-full transition-all duration-300"
            onClick={onClick}
        >
            <Card className="overflow-hidden border-none shadow-xl bg-card/40 backdrop-blur-md glass-dark h-full flex flex-col cursor-pointer hover:shadow-glow transition-shadow duration-500">
                <div className="relative aspect-[3/4] w-full bg-secondary/20 block">
                    <Image
                        src={paddle.image}
                        alt={paddle.name}
                        fill
                        className="object-cover transition-transform duration-500 hover:scale-110"
                        sizes="(max-width: 768px) 50vw, 33vw"
                    />
                    <div className="absolute top-2 left-2 flex flex-col gap-1">
                        <Badge variant="secondary" className="backdrop-blur-md bg-white/80 dark:bg-black/60 text-black dark:text-white font-bold border-none">
                            {paddle.brand}
                        </Badge>
                        {paddle.availableInBrazil === false && (
                            <Badge className="bg-amber-500 text-white border-none font-bold uppercase tracking-tighter text-[9px]">
                                Importado
                            </Badge>
                        )}
                        {paddle.powerLevel === 'High' && (
                            <Badge className="bg-primary text-primary-foreground border-none font-bold">
                                <Zap className="w-3 h-3 mr-1 fill-current" /> POWER
                            </Badge>
                        )}
                        {paddle.controlLevel === 'High' && (
                            <Badge className="bg-blue-500 text-white border-none font-bold">
                                <Shield className="w-3 h-3 mr-1 fill-current" /> CONTROL
                            </Badge>
                        )}
                        {paddle.swingWeight && (
                            <Badge className="bg-purple-500 text-white border-none font-bold">
                                <Activity className="w-3 h-3 mr-1" /> SW {paddle.swingWeight}
                            </Badge>
                        )}
                    </div>
                </div>
                <CardContent className="p-4 flex-grow">
                    <h3 className="font-bold text-base line-clamp-2 leading-tight mb-2">
                        {paddle.name}
                    </h3>

                    <div className="grid grid-cols-2 gap-2 mb-3">
                        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-medium uppercase tracking-wider">
                            <Weight className="w-3 h-3" />
                            {paddle.weight}
                        </div>
                        <div className="flex items-center gap-1 text-[10px] text-yellow-500 font-bold uppercase tracking-wider ml-auto">
                            <Star className="w-3 h-3 fill-current" />
                            {paddle.rating.toFixed(1)}
                        </div>
                    </div>

                    <p className="text-[10px] text-muted-foreground line-clamp-1 italic mb-4">
                        {paddle.surfaceMaterial}
                    </p>

                    {paddle.swingWeight && (
                        <WeightSensationScale swingWeight={paddle.swingWeight} className="mb-4" />
                    )}

                    {paddle.matchReasons && paddle.matchReasons.length > 0 && (
                        <div className="mt-2 space-y-1">
                            {paddle.matchReasons.slice(0, 2).map((reason, i) => (
                                <div key={i} className="text-[9px] text-primary-text flex items-center gap-1 font-medium bg-primary/5 p-1 rounded">
                                    <div className="w-1 h-1 rounded-full bg-primary" />
                                    {reason}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
                <CardFooter className="p-4 pt-0 mt-auto flex items-center justify-between">
                    <div className="flex flex-col">
                        <span className="font-black text-xl text-primary-text">
                            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(paddle.price)}
                        </span>
                    </div>
                    {onCompare && (
                        <Button
                            variant={isComparing ? "secondary" : "outline"}
                            size="sm"
                            className={`rounded-xl font-bold h-8 px-3 transition-all relative z-10 ${isComparing ? 'bg-primary text-primary-foreground border-none scale-105 shadow-glow-sm' : 'border-white/10 hover:bg-white/5'}`}
                            onClick={(e: React.MouseEvent) => {
                                e.stopPropagation();
                                e.preventDefault();
                                onCompare(paddle);
                            }}
                        >
                            {isComparing ? 'Comparando' : 'Comparar'}
                        </Button>
                    )}
                </CardFooter>
            </Card>
        </motion.div>
    );
}
