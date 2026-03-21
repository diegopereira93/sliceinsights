'use client';

import { motion } from 'framer-motion';
import { ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CatalogPaddle } from '@/types/catalog';

interface CatalogPaddleCardProps {
  paddle: CatalogPaddle;
  index: number;
}

export function CatalogPaddleCard({ paddle, index }: CatalogPaddleCardProps) {
  const cheapestOffer = paddle.market_offers[0];

  return (
    <motion.div
      className="glass-card rounded-xl overflow-hidden hover:ring-2 hover:ring-primary/30 transition-all duration-500"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <div className="aspect-[4/5] overflow-hidden">
        <img
          src={paddle.image_url ?? '/placeholder-paddle.png'}
          alt={paddle.model_name}
          loading="lazy"
          className="object-cover w-full h-full"
        />
      </div>
      <div className="p-4 space-y-2">
        <div className="flex gap-2 flex-wrap">
          {paddle.brand && (
            <Badge variant="outline" className="text-xs font-bold">
              {paddle.brand}
            </Badge>
          )}
          {paddle.specs.core_thickness_mm && (
            <Badge variant="outline" className="text-xs font-bold">
              {paddle.specs.core_thickness_mm}mm
            </Badge>
          )}
          {paddle.specs.surface_material && (
            <Badge variant="outline" className="text-xs font-bold">
              {paddle.specs.surface_material}
            </Badge>
          )}
        </div>
        <h3 className="text-base font-bold text-foreground leading-tight">
          {paddle.model_name}
        </h3>
        {cheapestOffer && (
          <p className="text-sm text-muted-foreground">
            A partir de{' '}
            <span className="text-primary font-bold">
              R$ {cheapestOffer.price_brl.toLocaleString('pt-BR')}
            </span>
          </p>
        )}
        {cheapestOffer && (
          <a
            href={cheapestOffer.store_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button
              size="sm"
              className="w-full rounded-xl font-bold text-xs bg-primary text-primary-foreground"
            >
              <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
              Ver na {cheapestOffer.store_name}
            </Button>
          </a>
        )}
      </div>
    </motion.div>
  );
}
