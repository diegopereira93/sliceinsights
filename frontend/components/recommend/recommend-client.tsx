'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { getApiBaseUrl } from '@/lib/api';
import { RecommendationResult, PaddleRecommendation, ChatMessage } from '@/types/recommend';

type Step = 0 | 1 | 2 | 'result';

interface WizardState {
  skill_level: 'beginner' | 'intermediate' | 'advanced' | null;
  play_style: 'power' | 'control' | 'balanced' | null;
  budget_max_brl: number | null;
  has_tennis_elbow: boolean;
  weight_preference: 'heavy' | 'standard' | 'light' | 'no_preference' | null;
}

export function RecommendClient() {
  const [step, setStep] = useState<Step>(0);
  const [wizardState, setWizardState] = useState<WizardState>({
    skill_level: null,
    play_style: null,
    budget_max_brl: null,
    has_tennis_elbow: false,
    weight_preference: null,
  });
  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat when messages change
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTo({
        top: chatScrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages.length]);

  const handleSubmit = async () => {
    setIsLoading(true);
    setNetworkError(null);
    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skill_level: wizardState.skill_level,
          play_style: wizardState.play_style,
          budget_max_brl: wizardState.budget_max_brl,
          has_tennis_elbow: wizardState.has_tennis_elbow,
          weight_preference: wizardState.weight_preference,
          limit: 3,
        }),
      });
      if (res.status === 429) {
        setNetworkError('Limite de requisicoes atingido. Aguarde um momento.');
        return;
      }
      if (!res.ok) throw new Error('API error');
      const data: RecommendationResult = await res.json();
      setResult(data);
      setStep('result');
      if (data.grok_dossier) {
        setMessages([{ role: 'assistant', content: data.grok_dossier }]);
      }
    } catch {
      setNetworkError('Erro ao buscar recomendacoes. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !result) return;

    const userMessage = chatInput;
    setChatInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsChatLoading(true);

    const context = result.recommendations
      .map(
        (r) =>
          `${r.brand_name} ${r.model_name}: preco a partir de R$${
            r.min_price_brl?.toFixed(2) ?? 'N/A'
          }, ` +
          `razoes: ${r.match_reasons.join(', ')}. ` +
          `Lojas: ${r.market_offers
            .map(
              (o) =>
                `${o.store_name} R$${o.price_brl.toFixed(2)} ${o.store_url}`
            )
            .join('; ')}`
      )
      .join('\n\n');

    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/recommend/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, { role: 'user', content: userMessage }],
          context,
        }),
      });
      if (!res.ok) throw new Error('Chat error');
      const data = { reply: '' };
      const jsonData = await res.json();
      if (jsonData.reply) {
        data.reply = jsonData.reply;
      }
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.reply || 'Erro de conexao. Tente novamente.' },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Erro de conexao. Tente novamente.' },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const resetWizard = () => {
    setStep(0);
    setWizardState({
      skill_level: null,
      play_style: null,
      budget_max_brl: null,
      has_tennis_elbow: false,
      weight_preference: null,
    });
    setResult(null);
    setMessages([]);
    setNetworkError(null);
  };

  // Render skeleton loading cards
  const renderSkeletons = () => (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={cn(
            'rounded-xl border border-border bg-muted p-4 animate-pulse',
            i === 1 && 'border-2 border-primary'
          )}
        >
          <div className="h-48 bg-border rounded-lg mb-4" />
          <div className="h-4 bg-border rounded w-3/4 mb-2" />
          <div className="h-3 bg-border rounded w-1/2 mb-4" />
          <div className="h-3 bg-border rounded w-full mb-2" />
          <div className="h-3 bg-border rounded w-full" />
        </div>
      ))}
    </div>
  );

  // Render recommendation cards
  const renderCards = (recommendations: PaddleRecommendation[]) => {
    if (recommendations.length === 0) {
      return (
        <Card className="border-border bg-muted text-center p-6">
          <CardContent className="pt-0">
            <p className="text-muted-foreground mb-4">
              {result?.grok_dossier || 'Nenhuma raquete encontrada para seu perfil.'}
            </p>
            <Button
              onClick={resetWizard}
              className="bg-primary text-primary-foreground font-black rounded-2xl"
            >
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      );
    }

    return (
      <div className="space-y-4">
        {recommendations.map((rec, index) => {
          const isFirst = rec.rank === 1;
          const imageUrl =
            rec.image_url ||
            `https://placehold.co/400x533/111111/ceff00?text=${encodeURIComponent(rec.model_name)}`;

          return (
            <motion.div
              key={rec.paddle_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card
                className={cn(
                  'glass-card border-none overflow-hidden group hover:ring-2 hover:ring-primary/30',
                  isFirst && 'ring-2 ring-primary'
                )}
              >
                <CardContent className="p-4">
                  {isFirst && (
                    <Badge className="bg-primary text-primary-foreground font-bold mb-2">
                      Match Perfeito
                    </Badge>
                  )}
                  <img
                    src={imageUrl}
                    alt={`${rec.brand_name} ${rec.model_name}`}
                    className="w-full h-48 object-contain rounded-lg mb-4 bg-background"
                  />
                  <h2 className="text-lg font-bold text-foreground">{rec.brand_name}</h2>
                  <h3 className="text-sm text-muted-foreground mb-2">{rec.model_name}</h3>
                  {rec.match_reasons.length > 0 && (
                    <ul className="text-xs text-muted-foreground mb-3 space-y-1">
                      {rec.match_reasons.map((reason, i) => (
                        <li key={i}>• {reason}</li>
                      ))}
                    </ul>
                  )}
                  {rec.tags && rec.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {rec.tags.map((tag, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {rec.market_offers.length > 0 && (
                    <div className="space-y-2">
                      {rec.market_offers.map((offer, i) => (
                        <div key={i} className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">{offer.store_name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-foreground">
                              R$ {offer.price_brl.toFixed(2)}
                            </span>
                            <Button
                              asChild
                              size="sm"
                              className="bg-primary text-primary-foreground rounded-lg text-xs"
                            >
                              <a
                                href={offer.store_url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                Comprar
                              </a>
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    );
  };

  return (
    <main className="min-h-screen bg-background text-foreground px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Step progress indicator */}
        {step !== 'result' && (
          <div className="flex gap-2 mb-6">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={cn(
                  'h-1 flex-1 rounded-full transition-colors',
                  i <= (typeof step === 'number' ? step : 3) ? 'bg-primary' : 'bg-border'
                )}
              />
            ))}
          </div>
        )}

        {step !== 'result' && (
          <>
            <h1 className="text-2xl font-bold mb-2 text-foreground">Encontre sua Raquete Ideal</h1>
            <p className="text-sm text-muted-foreground mb-6">Responda 3 perguntas rapidas</p>
          </>
        )}

        <AnimatePresence mode="wait">
          {/* Step 0: Skill Level + Play Style */}
          {step === 0 && (
            <motion.div
              key="step-0"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-3 text-foreground">
                    Qual seu nivel de jogo?
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                      <Button
                        key={level}
                        variant="outline"
                        onClick={() =>
                          setWizardState((prev) => ({ ...prev, skill_level: level }))
                        }
                        className={cn(
                          'rounded-full font-black transition-all',
                          wizardState.skill_level === level
                            ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                            : 'border-border text-muted-foreground hover:border-foreground/50'
                        )}
                      >
                        {level === 'beginner' && 'Iniciante'}
                        {level === 'intermediate' && 'Intermediario'}
                        {level === 'advanced' && 'Avancado'}
                      </Button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-3 text-foreground">
                    Qual seu estilo de jogo?
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {(['power', 'control', 'balanced'] as const).map((style) => (
                      <Button
                        key={style}
                        variant="outline"
                        onClick={() =>
                          setWizardState((prev) => ({ ...prev, play_style: style }))
                        }
                        className={cn(
                          'rounded-full font-black transition-all',
                          wizardState.play_style === style
                            ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                            : 'border-border text-muted-foreground hover:border-foreground/50'
                        )}
                      >
                        {style === 'power' && 'Potencia'}
                        {style === 'control' && 'Controle'}
                        {style === 'balanced' && 'Equilibrado'}
                      </Button>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={() => setStep(1)}
                  disabled={!wizardState.skill_level || !wizardState.play_style}
                  className="w-full bg-primary text-primary-foreground font-black rounded-2xl"
                  size="lg"
                >
                  Proximo
                </Button>
              </div>
            </motion.div>
          )}

          {/* Step 1: Budget */}
          {step === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-3 text-foreground">
                    Orcamento maximo (R$)
                  </label>
                  <Input
                    type="number"
                    placeholder="Ex: 1500"
                    min={100}
                    max={10000}
                    value={wizardState.budget_max_brl ?? ''}
                    onChange={(e) =>
                      setWizardState((prev) => ({
                        ...prev,
                        budget_max_brl: e.target.value ? Number(e.target.value) : null,
                      }))
                    }
                    className="bg-muted border-border focus:ring-primary rounded-xl"
                  />
                  <Button
                    variant="outline"
                    onClick={() =>
                      setWizardState((prev) => ({ ...prev, budget_max_brl: null }))
                    }
                    className={cn(
                      'mt-2 rounded-full font-black transition-all',
                      wizardState.budget_max_brl === null
                        ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                        : 'border-border text-muted-foreground hover:border-foreground/50'
                    )}
                  >
                    Sem limite de orcamento
                  </Button>
                </div>

                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setStep(0)}
                    className="flex-1 border-border text-muted-foreground hover:text-foreground rounded-xl"
                    size="lg"
                  >
                    Voltar
                  </Button>
                  <Button
                    onClick={() => setStep(2)}
                    className="flex-1 bg-primary text-primary-foreground font-black rounded-2xl"
                    size="lg"
                  >
                    Proximo
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 2: Health + Weight */}
          {step === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="space-y-6">
                <div>
                  <label className="flex items-center gap-3 mb-4 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={wizardState.has_tennis_elbow}
                      onChange={(e) =>
                        setWizardState((prev) => ({
                          ...prev,
                          has_tennis_elbow: e.target.checked,
                        }))
                      }
                      className="w-5 h-5 rounded border-border bg-muted text-primary focus:ring-primary focus:ring-offset-0"
                    />
                    <span className="text-sm text-foreground">
                      Tenho epicondilite (cotovelo de tenista)
                    </span>
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-3 text-foreground">
                    Preferencia de peso (opcional)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {(['heavy', 'standard', 'light', 'no_preference'] as const).map((weight) => (
                      <Button
                        key={weight}
                        variant="outline"
                        onClick={() =>
                          setWizardState((prev) => ({ ...prev, weight_preference: weight }))
                        }
                        className={cn(
                          'rounded-full font-black transition-all',
                          wizardState.weight_preference === weight
                            ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                            : 'border-border text-muted-foreground hover:border-foreground/50'
                        )}
                      >
                        {weight === 'heavy' && 'Pesada'}
                        {weight === 'standard' && 'Padrao'}
                        {weight === 'light' && 'Leve'}
                        {weight === 'no_preference' && 'Sem preferencia'}
                      </Button>
                    ))}
                  </div>
                </div>

                {networkError && (
                  <p className="text-red-400 text-sm mt-2">{networkError}</p>
                )}

                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => setStep(1)}
                    className="flex-1 border-border text-muted-foreground hover:text-foreground rounded-xl"
                    size="lg"
                  >
                    Voltar
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="flex-1 bg-primary text-primary-foreground font-black rounded-2xl"
                    size="lg"
                  >
                    {isLoading ? 'Buscando...' : 'Ver Recomendacoes'}
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading State */}
        {step !== 'result' && isLoading && (
          <div className="mt-8">
            <p className="text-sm text-muted-foreground mb-4">Analisando seu perfil...</p>
            {renderSkeletons()}
          </div>
        )}

        {/* Result State */}
        {step === 'result' && result && (
          <div className="space-y-6">
            {renderCards(result.recommendations)}

            {/* Chat Panel */}
            {messages.length > 0 && (
              <section className="mt-8 border border-border rounded-xl bg-muted max-h-[400px] flex flex-col">
                <div className="p-4 border-b border-border flex items-center gap-2">
                  <span className="text-sm font-semibold text-foreground">Consultor IA</span>
                </div>
                <div
                  ref={chatScrollRef}
                  className="flex-1 overflow-y-auto p-4 space-y-4"
                >
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={cn(
                        msg.role === 'assistant'
                          ? 'text-sm text-muted-foreground'
                          : 'text-sm text-foreground text-right'
                      )}
                    >
                      <div
                        className={cn(
                          'rounded-lg p-3 inline-block max-w-[85%]',
                          msg.role === 'assistant'
                            ? 'bg-muted border border-border'
                            : 'bg-primary/20 ml-auto'
                        )}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {isChatLoading && (
                    <div className="text-sm text-muted-foreground animate-pulse">Pensando...</div>
                  )}
                </div>
                <form
                  onSubmit={handleChatSubmit}
                  className="p-3 border-t border-border flex gap-2"
                >
                  <Input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Pergunte sobre as raquetes..."
                    className="bg-muted border-border focus:ring-primary rounded-xl flex-1"
                  />
                  <Button
                    type="submit"
                    variant="default"
                    size="icon"
                    disabled={!chatInput.trim() || isChatLoading}
                    className="bg-primary text-primary-foreground"
                  >
                    <span className="text-xs font-bold">→</span>
                  </Button>
                </form>
              </section>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
