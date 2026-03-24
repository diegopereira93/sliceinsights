'use client';

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronRight, 
  Target, 
  Activity, 
  DollarSign, 
  Dumbbell,
  Send,
  ArrowRight,
  Sparkles,
  User
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getRecommendations, RecommendationRequest, captureLead, mapBackendToFrontendPaddle } from "@/lib/api";
import { Paddle } from "@/types/paddle";

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
      { value: "balanced", label: "Equilibrado", desc: "Um pouco de tudo, adaptável" }
    ]
  },
  {
    id: "budget",
    title: "Qual o seu orçamento?",
    icon: DollarSign,
    options: [
      { value: "300", label: "Até R$ 300", desc: "Custo-benefício máximo" },
      { value: "600", label: "R$ 300 - R$ 600", desc: "Gama média, materiais de qualidade" },
      { value: "900", label: "R$ 600 - R$ 900", desc: "Raquetes premium de performance" },
      { value: "2000", label: "Acima de R$ 900", desc: "Top de linha absoluto" }
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

interface QuizAnswers {
  skillLevel?: string;
  playStyle?: string;
  budget?: string;
  competitionLevel?: string;
}

export default function QuizPage() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<QuizAnswers>({});
  const [showLead, setShowLead] = useState(false);
  const [leadForm, setLeadForm] = useState({ name: "", email: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recommendation, setRecommendation] = useState<Paddle | null>(null);

  const handleOptionSelect = (id: string, value: string) => {
    setAnswers(prev => ({ ...prev, [id]: value }));

    if (step < QUESTIONS.length - 1) {
      setTimeout(() => setStep(step + 1), 300);
    } else {
      setTimeout(() => setShowLead(true), 300);
    }
  };

  const handleLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadForm.name || !leadForm.email) return;

    setIsSubmitting(true);

    try {
      const request: RecommendationRequest = {
        skill_level: (answers.skillLevel as 'beginner' | 'intermediate' | 'advanced') || 'intermediate',
        play_style: answers.playStyle as 'power' | 'control' | 'balanced' || 'balanced',
        has_tennis_elbow: false,
        budget_max_brl: parseInt(answers.budget || "600"),
        limit: 1
      };

      const result = await getRecommendations(request);
      
      if (result.data && result.data.length > 0) {
        setRecommendation(mapBackendToFrontendPaddle(result.data[0]));
      }

      await captureLead(leadForm.email, leadForm.name);
    } catch (error) {
      console.error("Erro ao processar:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const progress = (step / QUESTIONS.length) * 100;

  if (recommendation) {
    return (
      <div className="min-h-screen pt-12 pb-32 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4"
            >
              <Sparkles className="w-10 h-10 text-primary" />
            </motion.div>
            <h1 className="text-3xl md:text-5xl font-black italic text-white mb-4">SUA RAQUETE IDEAL</h1>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              Analisamos seu perfil e encontramos a combinação perfeita de potência, controle e sensibilidade para o seu jogo.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-3xl">
            <div className="flex flex-col md:flex-row gap-8">
              <div className="md:w-1/3">
                <div className="aspect-[3/4] relative bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-2xl overflow-hidden">
                  {recommendation.image ? (
                    <img 
                      src={recommendation.image} 
                      alt={recommendation.name}
                      className="w-full h-full object-contain p-4"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-6xl font-black text-zinc-700">
                      {recommendation.brand}
                    </div>
                  )}
                </div>
              </div>

              <div className="md:w-2/3 space-y-6">
                <div>
                  <p className="text-sm font-bold text-primary tracking-widest uppercase mb-1">{recommendation.brand}</p>
                  <h2 className="text-2xl font-black text-white mb-4">{recommendation.name}</h2>
                  
                  <div className="flex flex-wrap gap-2 mb-6">
                    <span className="px-3 py-1 bg-white/10 rounded-full text-xs font-medium text-white">
                      {recommendation.coreThicknessmm}mm
                    </span>
                    <span className="px-3 py-1 bg-white/10 rounded-full text-xs font-medium text-white">
                      {recommendation.weight}g
                    </span>
                    {recommendation.powerLevel && (
                      <span className="px-3 py-1 bg-primary/20 text-primary rounded-full text-xs font-bold">
                        Power {recommendation.powerLevel}
                      </span>
                    )}
                    {recommendation.controlLevel && (
                      <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-bold">
                        Control {recommendation.controlLevel}
                      </span>
                    )}
                  </div>
                </div>

                <div className="glass-panel p-4 rounded-xl bg-white/5">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3">
                    <User className="text-primary w-5 h-5" />
                    Por que esta raquete?
                  </h3>
                  <p className="text-zinc-300 leading-relaxed">
                    Baseado no seu perfil de {answers.skillLevel === 'beginner' ? 'iniciante' : answers.skillLevel === 'intermediate' ? 'intermediário' : 'avançado'}, 
                    {" "}jogador {answers.playStyle === 'power' ? 'de potência' : answers.playStyle === 'control' ? 'de controle' : 'equilibrado'}, 
                    {" "}esta raquete oferece o equilíbrio ideal para o seu nível de jogo.
                  </p>
                </div>

                {recommendation.price && (
                  <div className="text-right">
                    <p className="text-sm text-zinc-500 mb-1">A partir de</p>
                    <p className="text-3xl font-black text-primary">
                      R$ {recommendation.price.toLocaleString('pt-BR')}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8 text-center">
            <Button 
              onClick={() => window.location.href = '/'}
              className="bg-primary text-primary-foreground font-bold px-8 py-4 rounded-xl"
            >
              Explorar Catálogo
              <ChevronRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-12 pb-32 flex flex-col items-center">
      <div className="w-full max-w-2xl px-4">
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

        {showLead ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-8 md:p-12 rounded-3xl"
          >
            <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mb-6 border border-primary/30">
              <Send className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-3xl font-black italic text-white mb-4">ANÁLISE CONCLUÍDA</h2>
            <p className="text-zinc-400 mb-8">
              Nossa inteligência artificial processou seu perfil de jogador. Para onde devemos enviar o relatório detalhado e a sua recomendação ideal?
            </p>

            <form onSubmit={handleLeadSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Seu Nome</label>
                <Input
                  required
                  type="text"
                  value={leadForm.name}
                  onChange={e => setLeadForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full bg-zinc-900 border-white/10 rounded-xl px-4 py-4 text-white focus:border-primary"
                  placeholder="Ex: João Silva"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Seu Email</label>
                <Input
                  required
                  type="email"
                  value={leadForm.email}
                  onChange={e => setLeadForm(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full bg-zinc-900 border-white/10 rounded-xl px-4 py-4 text-white focus:border-primary"
                  placeholder="Ex: joao@exemplo.com"
                />
              </div>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-4 bg-primary text-primary-foreground font-bold py-4 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isSubmitting ? "PROCESSANDO..." : "REVELAR MINHA RAQUETE"}
                {!isSubmitting && <ArrowRight className="w-5 h-5" />}
              </Button>
            </form>
          </motion.div>
        ) : (
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
                                {answers[q.id as keyof QuizAnswers] === opt.value && (
                                  <div className="w-2 h-2 bg-black rounded-full" />
                                )}
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
