import { createContext, useContext, useState, ReactNode } from "react";
import { Paddle } from "../lib/types/paddle";

interface BattleContextType {
  selectedPaddles: Paddle[];
  addPaddle: (paddle: Paddle) => void;
  removePaddle: (id: number) => void;
  clearBattle: () => void;
  isBattleModeOpen: boolean;
  setBattleModeOpen: (isOpen: boolean) => void;
}

const BattleContext = createContext<BattleContextType | undefined>(undefined);

export function BattleProvider({ children }: { children: ReactNode }) {
  const [selectedPaddles, setSelectedPaddles] = useState<Paddle[]>([]);
  const [isBattleModeOpen, setBattleModeOpen] = useState(false);

  const addPaddle = (paddle: Paddle) => {
    if (selectedPaddles.length < 4 && !selectedPaddles.find((p) => p.id === paddle.id)) {
      setSelectedPaddles((prev) => [...prev, paddle]);
      setBattleModeOpen(true);
    }
  };

  const removePaddle = (id: number) => {
    setSelectedPaddles((prev) => {
      const next = prev.filter((p) => p.id !== id);
      if (next.length === 0) setBattleModeOpen(false);
      return next;
    });
  };

  const clearBattle = () => {
    setSelectedPaddles([]);
    setBattleModeOpen(false);
  };

  return (
    <BattleContext.Provider
      value={{
        selectedPaddles,
        addPaddle,
        removePaddle,
        clearBattle,
        isBattleModeOpen,
        setBattleModeOpen,
      }}
    >
      {children}
    </BattleContext.Provider>
  );
}

export function useBattle() {
  const context = useContext(BattleContext);
  if (context === undefined) {
    throw new Error("useBattle must be used within a BattleProvider");
  }
  return context;
}
