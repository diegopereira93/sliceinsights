import { Link, useLocation } from "wouter";
import { Home, Sparkles, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function BottomNav() {
  const [location] = useLocation();

  const navItems = [
    { path: "/", label: "Home", icon: Home, ariaLabel: "Inicio" },
    { path: "/recommend", label: "AI Coach", icon: Sparkles, ariaLabel: "Recomendacao" },
    { path: "/statistics", label: "Análise", icon: BarChart2, ariaLabel: "Analise" },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 pb-safe">
      {/* Gradient fade to prevent sharp cutoff on scroll */}
      <div className="absolute bottom-full left-0 right-0 h-12 bg-gradient-to-t from-background to-transparent pointer-events-none" />
      
      <div className="glass-panel mx-4 mb-4 md:mb-6 rounded-2xl flex items-center justify-around p-2 max-w-md md:mx-auto">
        {navItems.map((item) => {
          const isActive = location === item.path || (item.path !== "/" && location.startsWith(item.path));
          
          return (
            <Link key={item.path} href={item.path} className="relative flex-1" aria-label={item.ariaLabel}>
              <div className="flex flex-col items-center justify-center py-2 px-4 cursor-pointer group">
                <item.icon
                  className={cn(
                    "w-6 h-6 mb-1 transition-all duration-300",
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-zinc-300"
                  )}
                />
                <span
                  className={cn(
                    "text-xs font-medium transition-colors",
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-zinc-300"
                  )}
                >
                  {item.label}
                </span>
                
                {isActive && (
                  <motion.div
                    layoutId="bottom-nav-indicator"
                    className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-8 h-1 bg-primary rounded-t-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-4 bg-primary/40 blur-md rounded-full" />
                  </motion.div>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
