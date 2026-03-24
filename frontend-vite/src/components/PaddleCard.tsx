import { ShoppingCart, Swords, Sparkles, Zap, Shield } from "lucide-react";
import { useBattle } from "./BattleContext";
import { motion } from "framer-motion";
import { WeightSensationScale } from "./WeightSensationScale";

interface PaddleCardProps {
  paddle: Paddle;
  index?: number;
}

function getSpinScore(paddle: Paddle): number {
  const base = paddle.controlScore ?? 5;
  const surfaceBonus = paddle.surface?.toLowerCase().includes("carbon") ? 2 : 0;
  return Math.min(10, Math.round(base * 0.7 + surfaceBonus + (paddle.coreThickness ?? 16) * 0.1));
}

interface StatBarProps {
  label: string;
  value: number;
  colorClass: string;
  icon?: React.ReactNode;
}

function StatBar({ label, value, colorClass, icon }: StatBarProps) {
  return (
    <div className="flex-1 flex flex-col gap-1.5">
      <div className="flex items-center gap-1">
        {icon && <span className="w-3 h-3">{icon}</span>}
        <span className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">{label}</span>
      </div>
      <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${colorClass}`}
          initial={{ width: 0 }}
          animate={{ width: `${(value / 10) * 100}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export function PaddleCard({ paddle, index = 0 }: PaddleCardProps) {
  const { addPaddle, selectedPaddles } = useBattle();
  const isSelectedForBattle = selectedPaddles.some(p => p.id === paddle.id);
  const spinScore = getSpinScore(paddle);

  const materialLabel = [paddle.surface, paddle.coreThickness ? `${paddle.coreThickness}mm` : null]
    .filter(Boolean)
    .join(" • ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="glass-card rounded-2xl overflow-hidden group flex flex-col h-full relative"
    >
      {paddle.isHiddenGem && (
        <div className="absolute top-3 right-3 z-10 bg-gradient-to-r from-primary to-emerald-400 text-black text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1 shadow-[0_0_15px_rgba(163,230,53,0.5)]">
          <Sparkles className="w-3 h-3" />
          JOIA RARA
        </div>
      )}

      {/* Image Container */}
      <div className="h-48 w-full bg-zinc-950/50 p-6 flex items-center justify-center relative overflow-hidden group-hover:bg-zinc-900 transition-colors">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/40 z-0" />
        {paddle.imageUrl ? (
          <img
            src={paddle.imageUrl}
            alt={paddle.name}
            className="h-full object-contain relative z-10 drop-shadow-2xl group-hover:scale-110 group-hover:rotate-3 transition-transform duration-500"
          />
        ) : (
          <div className="w-20 h-28 bg-zinc-800 border border-zinc-700 rounded-xl relative z-10 flex items-center justify-center group-hover:scale-105 transition-transform">
            <span className="font-display font-bold text-4xl text-zinc-600">{paddle.brand.charAt(0)}</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col">

        {/* Brand + Name */}
        <p className="text-[10px] font-bold text-primary tracking-widest uppercase mb-1">{paddle.brand}</p>
        <h3 className="font-display font-bold text-lg leading-tight line-clamp-2 mb-1">{paddle.name}</h3>

        {/* Material + Thickness subtitle */}
        {materialLabel && (
          <p className="text-xs text-zinc-500 mb-2">{materialLabel}</p>
        )}

        {/* Rating 5 stars */}
        {paddle.rating !== undefined && (
          <div className="flex items-center gap-1 mb-3">
            {[...Array(5)].map((_, i) => (
              <svg
                key={i}
                className={`w-3 h-3 ${i < Math.floor(paddle.rating ?? 0) ? 'text-primary fill-primary' : 'text-zinc-600'}`}
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            ))}
            {paddle.rating && <span className="text-xs text-zinc-400 ml-1">{paddle.rating.toFixed(1)}</span>}
          </div>
        )}

        {/* Price */}
        <p className="text-2xl font-light tracking-tight text-white mb-4">
          <span className="text-xs font-normal text-zinc-500 mr-1">a partir de</span>
          <span className="text-sm font-normal text-zinc-400 align-top mr-1">R$</span>
          {paddle.price.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
        </p>

        {/* 3 Bars side by side with icons */}
        <div className="flex gap-3 mb-4">
          <StatBar 
            label="PWR" 
            value={paddle.powerScore ?? 5} 
            colorClass="bg-gradient-to-r from-lime-500 to-lime-400"
            icon={<Zap className="w-3 h-3 text-lime-400" />}
          />
          <StatBar 
            label="CTRL" 
            value={paddle.controlScore ?? 5} 
            colorClass="bg-gradient-to-r from-cyan-500 to-cyan-400"
            icon={<Shield className="w-3 h-3 text-cyan-400" />}
          />
          <StatBar label="SPIN" value={spinScore} colorClass="bg-gradient-to-r from-purple-500 to-purple-400" />
        </div>

        {/* Weight Sensation Scale */}
        <div className="mb-4">
          <WeightSensationScale swingWeight={paddle.swingWeight} />
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-2 mt-auto">
          <button
            onClick={() => addPaddle(paddle)}
            disabled={isSelectedForBattle}
            className={`py-2.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all duration-300 ${
              isSelectedForBattle
                ? "bg-primary/20 text-primary border border-primary/30 cursor-not-allowed"
                : "bg-zinc-800 text-white hover:bg-zinc-700 border border-transparent"
            }`}
          >
            <Swords className="w-4 h-4" />
            {isSelectedForBattle ? "SELECIONADA ✓" : "COMPARAR"}
          </button>

          <a
            href={paddle.shopUrl || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="py-2.5 bg-white text-black hover:bg-primary rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-colors duration-300"
          >
            <ShoppingCart className="w-4 h-4" />
            COMPRAR
          </a>
        </div>
      </div>
    </motion.div>
  );
}
