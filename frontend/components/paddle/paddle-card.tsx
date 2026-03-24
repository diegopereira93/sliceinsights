'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Star, Zap, Shield, Weight, Activity, Swords } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { WeightSensationScale } from '@/components/ui/weight-sensation-scale';
import { Paddle } from '@/types/paddle';
import { cn } from '@/lib/utils';

interface PaddleCardProps {
  paddle: Paddle;
  onClick?: () => void;
  onCompare?: (paddle: Paddle) => void;
  isComparing?: boolean;
}

export function PaddleCard({ paddle, onClick, onCompare, isComparing }: PaddleCardProps) {
  const [hasError, setHasError] = useState(false);

  // Use price per mm of thickness as a "Value Index" (fun data insight)
  const valueIndex = paddle.coreThicknessmm ? (paddle.price / paddle.coreThicknessmm).toFixed(1) : null;

  return (
    <motion.div
      whileHover={{ y: -5 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
      className="cursor-pointer h-full"
    >
      <Card className="h-full border-none glass-card overflow-hidden group hover:ring-2 hover:ring-primary/30 transition-all duration-500">
        <CardContent className="p-0 relative aspect-[4/5] overflow-hidden">
          <Image
            src={hasError || !paddle.image ? '/placeholder-paddle.png' : paddle.image}
            alt={paddle.name}
            fill
            className="object-cover transition-transform duration-700 group-hover:scale-110"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            onError={() => setHasError(true)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity duration-500" />
          
          <div className="absolute top-4 left-4 flex flex-col gap-2">
            <Badge variant="secondary" className="bg-white/10 backdrop-blur-md border border-white/20 text-white font-black italic tracking-tighter uppercase">
              {paddle.brand}
            </Badge>
            {paddle.isSynthetic && (
                <Badge variant="outline" className="bg-amber-500/10 border-amber-500/20 text-amber-500 text-[9px] font-bold">
                    ESTIMATED SPECS
                </Badge>
            )}
          </div>


          <div className="absolute bottom-4 left-4 right-4 text-white">
            <div className="flex items-center gap-1.5 mb-1">
                <h3 className="text-xl font-black italic uppercase tracking-tighter leading-none">{paddle.name}</h3>
                {paddle.coreThicknessmm && (
                    <Badge className="bg-primary hover:bg-primary text-primary-foreground font-black text-[10px] h-5 px-1.5 shrink-0">
                        {paddle.coreThicknessmm}mm
                    </Badge>
                )}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`w-3 h-3 ${
                      i < Math.floor(paddle.rating)
                        ? 'text-primary fill-primary'
                        : 'text-white/20'
                    }`}
                  />
                ))}
              </div>
              <span className="text-xs font-bold text-white/60">{paddle.rating.toFixed(1)}</span>
            </div>
          </div>
        </CardContent>

        <CardFooter className="p-6 flex flex-col gap-5 bg-card/10 backdrop-blur-sm">
          {/* Main Stats Row */}
          <div className="grid grid-cols-2 gap-4 w-full">
            <div className="flex items-center justify-between p-2 rounded-xl bg-white/5 border border-white/5">
                <div className="flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5 text-primary" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest leading-none">Power</span>
                </div>
                <span className="text-sm font-black text-primary-text">{paddle.power}</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded-xl bg-white/5 border border-white/5">
                <div className="flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest leading-none">Control</span>
                </div>
                <span className="text-sm font-black text-primary-text">{paddle.control}</span>
            </div>
          </div>

          {/* Sensation Widget */}
          <WeightSensationScale swingWeight={paddle.swingWeight} />

          <div className="flex items-center justify-between w-full mt-2">
            <div className="flex flex-col">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">A partir de</span>
                <span className="text-2xl font-black text-primary-text tracking-tighter leading-none">
                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(paddle.price)}
                </span>
            </div>
            <Button 
                size="sm" 
                className={cn(
                    "rounded-xl font-black text-xs tracking-wider border-2 transition-all duration-300 group/compare",
                    isComparing 
                        ? "bg-primary text-primary-foreground border-primary shadow-[0_0_20px_rgba(206,255,0,0.4)] hover:bg-primary/90" 
                        : "bg-white/5 text-white border-white/10 hover:bg-primary/20 hover:border-primary/50 hover:text-primary"
                )}
                onClick={(e) => {
                    e.stopPropagation();
                    onCompare?.(paddle);
                }}
            >
                <Swords className={cn("w-4 h-4 mr-1.5 transition-transform group-hover/compare:rotate-12", isComparing && "animate-pulse")} />
                {isComparing ? 'SELECIONADA ✓' : 'COMPARAR'}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </motion.div>
  );
}
