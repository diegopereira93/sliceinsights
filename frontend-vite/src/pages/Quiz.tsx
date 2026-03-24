import { useState } from "react";
import { useGetQuizRecommendation, useCaptureLead, QuizAnswers } from "../lib/api-client";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Target, Activity, DollarSign, Dumbbell, User, Send, ArrowRight } from "lucide-react";
import { PaddleCard } from "@/components/PaddleCard";
import { Link } from "wouter";
import { cn } from "@/lib/utils";

const QUESTIONS = [
  {
    id: "skillLevel",
    title: "Qual o seu nível atual?",
    icon: Target,
    options: [
      { value: "beginner", label: "Iniciante", desc: "Começando agora ou jogo há poucos meses" },
      { value: "intermediate", label: "Intermediário", desc: "Jogo regularmente, participo de torneios locais" },
      { value: "advanced", label: "Avançado", desc: "Competidor de alto nível, DUPR 4.5+" }
    ]
  },
  {
    id: "playStyle",
    title: "Como você prefere jogar?",
    icon: Activity,
    options: [
      { value: "power", label: "Potência Bruta", desc: "Drives fortes do fundo da quadra" },
      { value: "control", label: "Controle & Precisão", desc: "Drops perfeitos, paciência na rede" },
      { value: "balanced", label: "Equilibrado", desc: "Um pouco de tudo, adaptável" },
      { value: "dinking", label: "Mestre do Dink", desc: "Jogo lento e estratégico na cozinha" }
    ]
  },
  {
    id: "budget",
    title: "Qual o seu orçamento?",
    icon: DollarSign,
    options: [
      { value: "under300", label: "Até R$ 300", desc: "Custo-benefício máximo" },
      { value: "300to600", label: "R$ 300 - R$ 600", desc: "Gama média, materiais de qualidade" },
      { value: "600to900", label: "R$ 600 - R$ 900", desc: "Raquetes premium de performance" },
      { value: "over900", label: "Acima de R$ 900", desc: "Top de linha absoluto" }
    ]
  },
  {
    id: "competitionLevel",
    title: "Com que frequência você compete?",
    icon: Dumbbell,
    options: [
      { value: "recreational", label: "Recreativo", desc: "Apenas por diversão com amigos" },
      { value: "club", label: "Clube/Liga", desc: "Jogos organizados semanalmente" },
      { value: "tournament", label: "Torneios", desc: "Viajo para competir a sério" }
    ]
  }
];

export default function Quiz() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Partial<QuizAnswers>>({});
  const [leadForm, setLeadForm] = useState({ name: "", email: "" });
  const [showLead, setShowLead] = useState(false);
  
  const recommendMutation = useGetQuizRecommendation();
  const captureLeadMutation = useCaptureLead();

  const handleOptionSelect = (key: string, value: string) => {
    setAnswers(prev => ({ ...prev, [key]: value }));
    
    if (step < QUESTIONS.length - 1) {
      setTimeout(() => setStep(step + 1), 300);
    } else {
      setTimeout(() => setShowLead(true), 300);
    }
  };

  const handleLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadForm.name || !leadForm.email) return;

    // Get recommendation
    const recResult = await recommendMutation.mutateAsync({
      data: answers as QuizAnswers
    });

    // Capture lead in background
    captureLeadMutation.mutate({
      data: {
        name: leadForm.name,
        email: leadForm.email,
        quizAnswers: answers as QuizAnswers,
        recommendedPaddleId: recResult.topPick.id
      }
    });
  };

  const progress = ((step) / QUESTIONS.length) * 100;

  // Render Results State
  if (recommendMutation.isSuccess && recommendMutation.data) {
    const { topPick, reasoning, alternatives } = recommendMutation.data;
    
    return (
      <div className="min-h-screen pt-12 pb-32 px-4 container mx-auto">
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <Sparkles className="w-10 h-10 text-primary" />
          </motion.div>
          <h1 className="text-3xl md:text-5xl font-display font-black text-white italic mb-4">SUA ARMA IDEAL</h1>
          <p className="text-zinc-400 max-w-2xl mx-auto">Analisamos seu perfil e encontramos a combinação perfeita de potência, controle e sensibilidade para o seu jogo.</p>
        </div>

        <div className="grid lg:grid-cols-12 gap-8 max-w-6xl mx-auto">
          <div className="lg:col-span-5">
            <PaddleCard paddle={topPick} />
          </div>
          
          <div className="lg:col-span-7 space-y-6">
            <div className="glass-panel p-6 rounded-2xl">
              <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                <User className="text-primary" />
                Por que esta raquete?
              </h3>
              <p className="text-zinc-300 leading-relaxed">{reasoning}</p>
            </div>
            
            <div className="glass-panel p-6 rounded-2xl bg-primary/5 border-primary/20">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">Quer aprofundar a análise?</h3>
                  <p className="text-sm text-zinc-400">Converse com o AI Coach sobre esta recomendação.</p>
                </div>
                <Link href="/chat">
                  <button className="p-4 bg-primary text-black rounded-xl hover:bg-white transition-colors">
                    <ChevronRight />
                  </button>
                </Link>
              </div>
            </div>

            {alternatives && alternatives.length > 0 && (
              <div>
                <h3 className="text-lg font-bold text-white mb-4 mt-8">Boas Alternativas</h3>
                <div className="grid grid-cols-2 gap-4">
                  {alternatives.map(alt => (
                    <div key={alt.id} className="bg-zinc-900 border border-white/5 rounded-xl p-3 flex gap-3 items-center">
                      <div className="w-12 h-16 bg-zinc-800 rounded flex-shrink-0 flex items-center justify-center p-1">
                        {alt.imageUrl ? <img src={alt.imageUrl} className="h-full object-contain"/> : alt.brand[0]}
                      </div>
                      <div>
                        <p className="text-xs text-primary font-bold">{alt.brand}</p>
                        <p className="text-sm font-bold text-white line-clamp-1">{alt.name}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-12 pb-32 flex flex-col items-center">
      <div className="w-full max-w-2xl px-4">
        
        {/* Progress Bar */}
        {!showLead && (
          <div className="mb-12">
            <div className="flex justify-between text-xs text-zinc-500 font-bold tracking-widest uppercase mb-4">
              <span>Racket Finder AI</span>
              <span>Passo {step + 1} de {QUESTIONS.length}</span>
            </div>
            <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-primary"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        )}

        {/* Lead Capture Form */}
        {showLead ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-8 md:p-12 rounded-3xl"
          >
            <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mb-6 border border-primary/30">
              <Send className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-3xl font-display font-black text-white italic mb-4">ANÁLISE CONCLUÍDA</h2>
            <p className="text-zinc-400 mb-8">Nossa inteligência artificial processou seu perfil de jogador. Para onde devemos enviar o relatório detalhado e a sua recomendação ideal?</p>
            
            <form onSubmit={handleLeadSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Seu Nome</label>
                <input 
                  required
                  type="text" 
                  value={leadForm.name}
                  onChange={e => setLeadForm(prev => ({...prev, name: e.target.value}))}
                  className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-4 text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                  placeholder="Ex: João Silva"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Seu Email</label>
                <input 
                  required
                  type="email" 
                  value={leadForm.email}
                  onChange={e => setLeadForm(prev => ({...prev, email: e.target.value}))}
                  className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-4 text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                  placeholder="Ex: joao@exemplo.com"
                />
              </div>
              <button 
                type="submit"
                disabled={recommendMutation.isPending}
                className="w-full mt-4 bg-primary text-black font-bold py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-white transition-colors disabled:opacity-50"
              >
                {recommendMutation.isPending ? "PROCESSANDO..." : "REVELAR MINHA RAQUETE"}
                {!recommendMutation.isPending && <ArrowRight className="w-5 h-5" />}
              </button>
            </form>
          </motion.div>
        ) : (
          /* Question Flow */
          <div className="relative min-h-[400px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
                className="absolute inset-0"
              >
                {(() => {
                  const q = QUESTIONS[step];
                  const Icon = q.icon;
                  return (
                    <>
                      <div className="flex items-center gap-4 mb-8">
                        <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                          <Icon className="w-6 h-6 text-primary" />
                        </div>
                        <h2 className="text-2xl md:text-3xl font-bold text-white">{q.title}</h2>
                      </div>

                      <div className="grid grid-cols-1 gap-4">
                        {q.options.map((opt) => (
                          <button
                            key={opt.value}
                            onClick={() => handleOptionSelect(q.id, opt.value)}
                            className={cn(
                              "text-left p-6 rounded-2xl border transition-all duration-300 group hover:-translate-y-1",
                              answers[q.id as keyof QuizAnswers] === opt.value 
                                ? "bg-primary/10 border-primary shadow-[0_0_20px_rgba(163,230,53,0.15)]" 
                                : "bg-zinc-900/50 border-white/10 hover:border-white/30 hover:bg-zinc-800"
                            )}
                          >
                            <div className="flex justify-between items-center">
                              <div>
                                <h4 className="text-lg font-bold text-white mb-1">{opt.label}</h4>
                                <p className="text-sm text-zinc-500">{opt.desc}</p>
                              </div>
                              <div className={cn(
                                "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors",
                                answers[q.id as keyof QuizAnswers] === opt.value
                                  ? "border-primary bg-primary"
                                  : "border-zinc-700 group-hover:border-zinc-500"
                              )}>
                                {answers[q.id as keyof QuizAnswers] === opt.value && <div className="w-2 h-2 bg-black rounded-full" />}
                              </div>
                            </div>
                          </button>
                        ))}
                      </div>
                    </>
                  );
                })()}
              </motion.div>
            </AnimatePresence>
          </div>
        )}

      </div>
    </div>
  );
}

// Reused sparkle icon
function Sparkles(props: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinelinejoin="round" {...props}>
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      <path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>
    </svg>
  )
}
