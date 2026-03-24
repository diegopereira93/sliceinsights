import { useState, useMemo, useEffect } from "react";
import { PaddleCard } from "@/components/PaddleCard";
import { Search, Loader2, Zap, Target, Scale, Layers, Gem } from "lucide-react";
import { motion, useMotionValue, animate } from "framer-motion";
import { Link } from "wouter";

type FilterId = "all" | "power" | "control" | "balanced" | "core-thin" | "core-mid" | "core-thick" | "gems";

interface Paddle {
  id: number;
  name: string;
  brand: string;
  price: number;
  imageUrl?: string;
  coreThickness?: number;
  surface?: string;
  powerScore: number;
  controlScore: number;
  isHiddenGem?: boolean;
}

interface SmartFilter {
  id: FilterId;
  label: string;
  icon: React.ReactNode;
  match: (p: Paddle) => boolean;
}

const SMART_FILTERS: SmartFilter[] = [
  { id: "all",        label: "Todos",          icon: null,                      match: () => true },
  { id: "power",      label: "⚡ Power",        icon: <Zap className="w-3 h-3"/>,  match: p => (p.powerScore ?? 0) >= 8 },
  { id: "control",    label: "🎯 Controle",     icon: <Target className="w-3 h-3"/>, match: p => (p.controlScore ?? 0) >= 8 },
  { id: "balanced",   label: "⚖️ Equilibrado",  icon: <Scale className="w-3 h-3"/>, match: p => Math.abs((p.powerScore ?? 5) - (p.controlScore ?? 5)) <= 1 },
  { id: "core-thin",  label: "12–14mm Speed",  icon: <Layers className="w-3 h-3"/>, match: p => (p.coreThickness ?? 16) <= 14 },
  { id: "core-mid",   label: "16mm Controle",  icon: <Layers className="w-3 h-3"/>, match: p => p.coreThickness === 16 },
  { id: "core-thick", label: "18mm+ Estabil.", icon: <Layers className="w-3 h-3"/>, match: p => (p.coreThickness ?? 16) >= 18 },
  { id: "gems",       label: "💎 Joias",        icon: <Gem className="w-3 h-3"/>,   match: p => !!p.isHiddenGem },
];

function FloatingPaddle() {
  const y = useMotionValue(0);

  useEffect(() => {
    const controls = animate(y, [0, -14, 0], {
      duration: 4,
      ease: "easeInOut",
      repeat: Infinity,
    });
    return controls.stop;
  }, [y]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1.2, type: "spring", damping: 20 }}
      className="hidden md:flex justify-center relative"
    >
      {/* Ambient lime glow beneath paddle */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-56 h-16 bg-primary/30 blur-[60px] rounded-full pointer-events-none" />
      {/* Radial depth halo */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-primary/10 blur-[120px] rounded-full pointer-events-none" />

      <motion.img
        src={`${import.meta.env.BASE_URL}images/cinematic-paddle-nobg.png`}
        alt="Premium Paddle"
        className="w-full max-w-[420px] relative z-10 select-none"
        style={{
          filter: "drop-shadow(0 0 32px rgba(163,230,53,0.45)) drop-shadow(0 40px 60px rgba(0,0,0,0.7)) drop-shadow(-6px -4px 20px rgba(163,230,53,0.2))",
        }}
        animate={{ y: [0, -14, 0] }}
        transition={{ duration: 4, ease: "easeInOut", repeat: Infinity }}
      />
    </motion.div>
  );
}

export default function Home() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterId>("all");
  const [paddles, setPaddles] = useState<Paddle[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchPaddles = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      try {
        setIsLoading(true);
        const response = await fetch(
          "/paddles?limit=100&available_in_brazil=true",
          {
            signal: controller.signal,
            headers: { "Accept": "application/json" },
          }
        );
        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`Failed to fetch paddles: ${response.status} ${response.statusText}`);
        }

        const responseData = await response.json();
        const paddlesArray = responseData.data || [];

        const mappedPaddles: Paddle[] = paddlesArray.map((p: Record<string, unknown>) => ({
          id: typeof p.id === 'string' ? parseInt(p.id.replace(/-/g, '').slice(0, 8), 16) : (p.id as number),
          name: (p.name as string) || (p.model_name as string) || "",
          brand: (p.brand as string) || (p.brand_name as string) || "",
          price: (p.price as number) || (p.min_price_brl as number) || 0,
          imageUrl: (p.imageUrl as string) || (p.image_url as string) || undefined,
          coreThickness: (p.coreThickness as number) || (p.specs as Record<string, unknown>)?.core_thickness_mm as number || undefined,
          surface: (p.surface as string) || (p.specs as Record<string, unknown>)?.face_material as string || undefined,
          powerScore: (p.powerScore as number) ?? (p.ratings as Record<string, number>)?.power ?? 0,
          controlScore: (p.controlScore as number) ?? (p.ratings as Record<string, number>)?.control ?? 0,
          isHiddenGem: (p.isHiddenGem as boolean) ?? (p.is_featured as boolean) ?? undefined,
        }));

        setPaddles(mappedPaddles);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          setError(new Error("Request timed out. Please try again."));
        } else {
          setError(err instanceof Error ? err : new Error("Unknown error"));
        }
      } finally {
        clearTimeout(timeoutId);
        setIsLoading(false);
      }
    };

    fetchPaddles();
  }, []);

  const filtered = useMemo(() => {
    const filterFn = SMART_FILTERS.find(f => f.id === activeFilter)?.match ?? (() => true);
    const searched = search.trim()
      ? paddles.filter(p =>
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.brand.toLowerCase().includes(search.toLowerCase()) ||
          (p.surface ?? "").toLowerCase().includes(search.toLowerCase())
        )
      : paddles;
    return searched.filter(filterFn);
  }, [paddles, search, activeFilter]);

  return (
    <div className="min-h-screen pb-32">

      {/* ── HERO ─────────────────────────────────────────── */}
      <section className="relative min-h-[580px] flex items-center overflow-hidden">

        {/* Mesh gradient background */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_70%_40%,rgba(163,230,53,0.07)_0%,transparent_70%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_40%_at_20%_70%,rgba(163,230,53,0.04)_0%,transparent_60%)]" />
          {/* Organic node network via SVG */}
          <svg className="absolute inset-0 w-full h-full opacity-[0.07]" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id="ng" cx="70%" cy="40%">
                <stop offset="0%" stopColor="#a3e635" />
                <stop offset="100%" stopColor="transparent" />
              </radialGradient>
            </defs>
            {[
              [80,120],[200,60],[350,180],[500,80],[650,150],[780,40],[920,200],[1100,90],[1200,160],
              [140,280],[320,320],[480,260],[660,300],[820,250],[1000,320],[1150,280],
              [60,420],[240,480],[420,420],[590,460],[760,410],[940,470],[1120,430],
            ].map(([x,y],i) => (
              <circle key={i} cx={x} cy={y} r="2.5" fill="#a3e635" />
            ))}
            {[[80,120,200,60],[200,60,350,180],[350,180,500,80],[500,80,650,150],[650,150,780,40],
              [780,40,920,200],[920,200,1100,90],[1100,90,1200,160],[200,60,140,280],[350,180,320,320],
              [500,80,480,260],[650,150,660,300],[780,40,820,250],[920,200,1000,320],[140,280,320,320],
              [320,320,480,260],[480,260,660,300],[660,300,820,250],[820,250,1000,320],[1000,320,1150,280],
              [140,280,60,420],[320,320,240,480],[480,260,420,420],[660,300,590,460],[820,250,760,410],
              [1000,320,940,470],[1150,280,1120,430],
            ].map(([x1,y1,x2,y2],i) => (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#a3e635" strokeWidth="0.6" />
            ))}
          </svg>
          <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-transparent to-background" />
        </div>

        {/* Hero content */}
        <div className="container relative z-10 mx-auto px-4 grid md:grid-cols-2 gap-8 items-center py-16">

          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.9, ease: "easeOut" }}
          >
            {/* Eyebrow */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="inline-flex items-center gap-2 text-primary text-xs font-bold tracking-[0.2em] uppercase mb-6 px-3 py-1.5 rounded-full border border-primary/30 bg-primary/5"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              INTELIGÊNCIA EM EQUIPAMENTO
            </motion.div>

            {/* Headline */}
            <h1 className="font-display font-black text-white leading-[0.92] tracking-[-0.03em] mb-6" style={{ fontSize: "clamp(3.2rem, 8vw, 6rem)" }}>
              DOMINE A<br />
              <span className="italic" style={{
                background: "linear-gradient(135deg, #a3e635 0%, #4ade80 50%, #a3e635 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                filter: "drop-shadow(0 0 40px rgba(163,230,53,0.4))",
              }}>
                QUADRA.
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-base md:text-lg text-zinc-300 max-w-md leading-relaxed mb-10 font-light">
              Analisamos as métricas de desempenho de centenas de raquetes
              para encontrar o <span className="text-white font-medium">match ideal</span> para o seu estilo de jogo.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap gap-4">
              <Link href="/quiz">
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  className="relative px-7 py-4 bg-primary text-black font-bold text-sm rounded-xl overflow-hidden"
                >
                  {/* Pulse ring */}
                  <span className="absolute inset-0 rounded-xl animate-ping bg-primary/30 pointer-events-none" style={{ animationDuration: "2.5s" }} />
                  <span className="relative z-10 tracking-wide">ENCONTRAR MINHA RAQUETE →</span>
                </motion.button>
              </Link>
              <a
                href="#catalog"
                className="px-7 py-4 rounded-xl text-sm font-semibold text-zinc-300 border border-white/10 hover:border-primary/40 hover:text-white hover:bg-white/5 transition-all duration-300 tracking-wide"
              >
                EXPLORAR CATÁLOGO
              </a>
            </div>
          </motion.div>

          <FloatingPaddle />
        </div>
      </section>

      {/* ── CATALOG ──────────────────────────────────────── */}
      <section id="catalog" className="container mx-auto px-4 -mt-4 relative z-20">

        {/* Glassmorphism filter panel */}
        <div
          className="rounded-2xl mb-8 p-4 md:p-5 flex flex-col gap-4"
          style={{
            background: "rgba(15,15,18,0.65)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(255,255,255,0.07)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
          }}
        >
          {/* Search row */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Buscar por nome, marca ou material..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/8 rounded-xl py-3 pl-11 pr-4 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-primary/50 focus:bg-white/[0.06] transition-all"
            />
          </div>

          {/* Smart filter pills */}
          <div className="flex gap-2 flex-wrap">
            {SMART_FILTERS.map(f => (
              <button
                key={f.id}
                onClick={() => setActiveFilter(f.id)}
                className={`whitespace-nowrap px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 ${
                  activeFilter === f.id
                    ? "bg-primary text-black shadow-[0_0_12px_rgba(163,230,53,0.35)]"
                    : "bg-white/[0.06] text-zinc-400 border border-white/[0.07] hover:border-primary/30 hover:text-zinc-200"
                }`}
              >
                {f.label}
              </button>
            ))}

            {/* Result count */}
            {!isLoading && (
              <span className="ml-auto self-center text-xs text-zinc-600 font-mono">
                {filtered.length} raquetes
              </span>
            )}
          </div>
        </div>

        {/* Results */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24">
            <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
            <p className="text-zinc-600 font-display tracking-[0.2em] uppercase text-xs">Carregando arsenal...</p>
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-400 font-medium mb-2">Erro ao carregar raquetes.</p>
            <p className="text-zinc-500 text-sm">{error.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-primary/20 text-primary rounded-lg text-sm hover:bg-primary/30 transition-colors"
            >
              Tentar novamente
            </button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <Search className="w-10 h-10 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-white mb-2">Nenhuma raquete encontrada</h3>
            <p className="text-zinc-500 text-sm">Tente ajustar os filtros de busca.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {filtered.map((paddle, idx) => (
              <PaddleCard key={paddle.id} paddle={paddle} index={idx} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
