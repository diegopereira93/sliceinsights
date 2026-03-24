import { motion, AnimatePresence } from "framer-motion";
import { X, Swords, ShoppingCart, Info } from "lucide-react";
import { useBattle } from "./BattleContext";
import { formatCurrency, cn } from "@/lib/utils";
import { Paddle } from "../lib/api-client";

export function BattleOverlay() {
  const { selectedPaddles, removePaddle, isBattleModeOpen, setBattleModeOpen, clearBattle: _clearBattle } = useBattle();

  if (!isBattleModeOpen || selectedPaddles.length === 0) return null;

  const handleShop = (url?: string) => {
    if (url) window.open(url, "_blank");
  };

  const getWinnerClass = (paddles: Paddle[], currentPaddleId: number, metric: 'powerScore' | 'controlScore' | 'price', lowerIsBetter = false) => {
    if (paddles.length < 2) return "";
    
    let bestVal = paddles[0][metric] || 0;
    paddles.forEach(p => {
      const val = p[metric] || 0;
      if (lowerIsBetter ? val < bestVal : val > bestVal) bestVal = val;
    });

    const currentVal = paddles.find(p => p.id === currentPaddleId)?.[metric];
    return currentVal === bestVal ? "text-primary font-bold shadow-[0_0_10px_rgba(163,230,53,0.3)] bg-primary/10 rounded px-1" : "";
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed inset-0 z-50 flex flex-col justify-end pointer-events-none"
      >
        <div className="glass-panel w-full h-[85vh] rounded-t-3xl flex flex-col pointer-events-auto border-t border-primary/30 relative overflow-hidden">
          
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-white/10 bg-zinc-950/80 backdrop-blur-xl z-10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/20 rounded-lg text-primary">
                <Swords className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-display font-bold text-white tracking-wide uppercase italic">
                  MODO DE BATALHA
                </h2>
                <p className="text-xs text-primary">{selectedPaddles.length} Raquetes Selecionadas</p>
              </div>
            </div>
            <button 
              onClick={() => setBattleModeOpen(false)}
              className="p-2 rounded-full hover:bg-white/10 transition-colors"
            >
              <X className="w-6 h-6 text-zinc-400" />
            </button>
          </div>

          {/* VS Content */}
          <div className="flex-1 overflow-x-auto overflow-y-hidden custom-scrollbar bg-black/40">
            <div className="flex h-full min-w-max p-6 gap-6 relative">
              
              {/* VS Overlay Decorators */}
              {selectedPaddles.length > 1 && selectedPaddles.slice(0, -1).map((_, idx) => (
                <div 
                  key={`vs-${idx}`}
                  className="absolute top-1/3 text-4xl font-display font-black text-zinc-800 italic opacity-50 z-0 pointer-events-none"
                  style={{ left: `calc(${((idx + 1) * 100) / selectedPaddles.length}% - 2rem)` }}
                >
                  VS
                </div>
              ))}

              {selectedPaddles.map((paddle) => (
                <div key={paddle.id} className="w-[300px] flex flex-col relative z-10">
                  <button 
                    onClick={() => removePaddle(paddle.id)}
                    className="absolute top-2 right-2 p-1.5 bg-black/50 hover:bg-destructive text-white rounded-full z-20 backdrop-blur-md transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                  
                  {/* Image & Header */}
                  <div className="bg-zinc-900/50 rounded-2xl p-4 border border-white/5 mb-4 flex flex-col items-center">
                    <div className="h-48 w-full relative mb-4 flex items-center justify-center">
                      {paddle.imageUrl ? (
                        <img src={paddle.imageUrl} alt={paddle.name} className="max-h-full object-contain drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)]" />
                      ) : (
                        <div className="w-24 h-32 bg-zinc-800 border-2 border-zinc-700 rounded-xl flex items-center justify-center font-display text-4xl font-bold text-zinc-600">
                          {paddle.brand.charAt(0)}
                        </div>
                      )}
                    </div>
                    <span className="text-xs font-bold text-primary tracking-wider uppercase mb-1">{paddle.brand}</span>
                    <h3 className="text-xl font-bold text-center leading-tight mb-2">{paddle.name}</h3>
                    <p className={cn("text-2xl font-display font-bold", getWinnerClass(selectedPaddles, paddle.id, 'price', true))}>
                      {formatCurrency(paddle.price)}
                    </p>
                    
                    <button 
                      onClick={() => handleShop(paddle.shopUrl)}
                      className="mt-4 w-full py-3 bg-white text-black font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-primary transition-colors"
                    >
                      <ShoppingCart className="w-4 h-4" />
                      COMPRAR AGORA
                    </button>
                  </div>

                  {/* Stats Comparison Rows */}
                  <div className="space-y-4 px-2">
                    <div>
                      <div className="flex justify-between text-xs text-zinc-400 mb-1">
                        <span>Poder</span>
                        <span className={getWinnerClass(selectedPaddles, paddle.id, 'powerScore')}>{paddle.powerScore}/100</span>
                      </div>
                      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-orange-500 rounded-full" style={{ width: `${paddle.powerScore}%` }} />
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-xs text-zinc-400 mb-1">
                        <span>Controle</span>
                        <span className={getWinnerClass(selectedPaddles, paddle.id, 'controlScore')}>{paddle.controlScore}/100</span>
                      </div>
                      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${paddle.controlScore}%` }} />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mt-6">
                      <div className="bg-zinc-900/50 p-3 rounded-xl border border-white/5">
                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Espessura</p>
                        <p className="font-bold text-sm">{paddle.coreThickness}mm</p>
                      </div>
                      <div className="bg-zinc-900/50 p-3 rounded-xl border border-white/5">
                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Peso (Sensa)</p>
                        <p className="font-bold text-sm truncate">{paddle.weightSensation || 'N/A'}</p>
                      </div>
                      <div className="bg-zinc-900/50 p-3 rounded-xl border border-white/5 col-span-2">
                        <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Superfície</p>
                        <p className="font-bold text-sm truncate">{paddle.surface || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {selectedPaddles.length < 4 && (
                <div className="w-[300px] flex items-center justify-center">
                  <div className="w-full h-full border-2 border-dashed border-white/10 rounded-2xl flex flex-col items-center justify-center text-zinc-500 gap-4">
                    <Info className="w-12 h-12 opacity-50" />
                    <p className="text-sm font-medium">Adicione outra raquete<br/>para comparar</p>
                  </div>
                </div>
              )}
            </div>
          </div>
          
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
