'use client';

import { useState, useRef, useEffect } from 'react';
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

export default function RecommendPage() {
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
          className={`rounded-xl border border-[#222222] bg-[#111111] p-4 animate-pulse ${
            i === 1 ? 'border-2 border-[#ceff00]' : ''
          }`}
        >
          <div className="h-48 bg-[#222222] rounded-lg mb-4" />
          <div className="h-4 bg-[#222222] rounded w-3/4 mb-2" />
          <div className="h-3 bg-[#222222] rounded w-1/2 mb-4" />
          <div className="h-3 bg-[#222222] rounded w-full mb-2" />
          <div className="h-3 bg-[#222222] rounded w-full" />
        </div>
      ))}
    </div>
  );

  // Render recommendation cards
  const renderCards = (recommendations: PaddleRecommendation[]) => {
    if (recommendations.length === 0) {
      return (
        <div className="border border-[#222222] rounded-xl p-6 bg-[#111111] text-center">
          <p className="text-gray-300 mb-4">{result?.grok_dossier || 'Nenhuma raquete encontrada para seu perfil.'}</p>
          <button
            onClick={resetWizard}
            className="bg-[#ceff00] text-black px-4 py-2 rounded-lg font-semibold hover:bg-[#b8e600] transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {recommendations.map((rec) => {
          const isFirst = rec.rank === 1;
          const imageUrl =
            rec.image_url ||
            `https://placehold.co/400x533/111111/ceff00?text=${encodeURIComponent(rec.model_name)}`;

          return (
            <div
              key={rec.paddle_id}
              className={`rounded-xl bg-[#111111] p-4 ${
                isFirst
                  ? 'border-2 border-[#ceff00]'
                  : 'border border-[#222222]'
              }`}
            >
              {isFirst && (
                <span className="bg-[#ceff00] text-black text-xs font-bold px-2 py-1 rounded-full inline-block mb-2">
                  Match Perfeito
                </span>
              )}
              <img
                src={imageUrl}
                alt={`${rec.brand_name} ${rec.model_name}`}
                className="w-full h-48 object-contain rounded-lg mb-4 bg-[#0a0a0a]"
              />
              <h2 className="text-lg font-bold">{rec.brand_name}</h2>
              <h3 className="text-sm text-gray-400 mb-2">{rec.model_name}</h3>
              {rec.match_reasons.length > 0 && (
                <ul className="text-xs text-gray-300 mb-3 space-y-1">
                  {rec.match_reasons.map((reason, i) => (
                    <li key={i}>• {reason}</li>
                  ))}
                </ul>
              )}
              {rec.market_offers.length > 0 && (
                <div className="space-y-2">
                  {rec.market_offers.map((offer, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">{offer.store_name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">
                          R$ {offer.price_brl.toFixed(2)}
                        </span>
                        <a
                          href={offer.store_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-[#ceff00] text-black text-sm px-3 py-1 rounded hover:bg-[#b8e600] transition-colors"
                        >
                          Comprar
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <main className="min-h-screen bg-[#000000] text-white px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {step !== 'result' && (
          <>
            <h1 className="text-2xl font-bold mb-2">Encontre sua Raquete Ideal</h1>
            <p className="text-sm text-gray-400 mb-6">Responda 3 perguntas rapidas</p>
          </>
        )}

        {/* Step 0: Skill Level + Play Style */}
        {step === 0 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-3">Qual seu nivel de jogo?</label>
              <div className="flex flex-wrap gap-2">
                {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                  <button
                    key={level}
                    onClick={() =>
                      setWizardState((prev) => ({ ...prev, skill_level: level }))
                    }
                    className={`px-4 py-2 rounded-full border transition-colors ${
                      wizardState.skill_level === level
                        ? 'border-[#ceff00] bg-[#ceff00]/10 text-[#ceff00]'
                        : 'border-[#222222] text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    {level === 'beginner' && 'Iniciante'}
                    {level === 'intermediate' && 'Intermediario'}
                    {level === 'advanced' && 'Avancado'}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-3">Qual seu estilo de jogo?</label>
              <div className="flex flex-wrap gap-2">
                {(['power', 'control', 'balanced'] as const).map((style) => (
                  <button
                    key={style}
                    onClick={() =>
                      setWizardState((prev) => ({ ...prev, play_style: style }))
                    }
                    className={`px-4 py-2 rounded-full border transition-colors ${
                      wizardState.play_style === style
                        ? 'border-[#ceff00] bg-[#ceff00]/10 text-[#ceff00]'
                        : 'border-[#222222] text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    {style === 'power' && 'Potencia'}
                    {style === 'control' && 'Controle'}
                    {style === 'balanced' && 'Equilibrado'}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => setStep(1)}
              disabled={!wizardState.skill_level || !wizardState.play_style}
              className="w-full bg-[#ceff00] text-black font-semibold px-6 py-3 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#b8e600] transition-colors"
            >
              Proximo
            </button>
          </div>
        )}

        {/* Step 1: Budget */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-3">Orcamento maximo (R$)</label>
              <input
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
                className="w-full bg-[#111111] border border-[#222222] rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#ceff00]"
              />
              <button
                onClick={() =>
                  setWizardState((prev) => ({ ...prev, budget_max_brl: null }))
                }
                className={`mt-2 px-4 py-2 rounded-full border transition-colors ${
                  wizardState.budget_max_brl === null
                    ? 'border-[#ceff00] bg-[#ceff00]/10 text-[#ceff00]'
                    : 'border-[#222222] text-gray-300 hover:border-gray-500'
                }`}
              >
                Sem limite de orcamento
              </button>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(0)}
                className="flex-1 px-4 py-3 rounded-lg border border-[#222222] text-gray-400 hover:text-white transition-colors"
              >
                Voltar
              </button>
              <button
                onClick={() => setStep(2)}
                className="flex-1 bg-[#ceff00] text-black font-semibold px-6 py-3 rounded-lg hover:bg-[#b8e600] transition-colors"
              >
                Proximo
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Health + Weight */}
        {step === 2 && (
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
                  className="w-5 h-5 rounded border-[#222222] bg-[#111111] text-[#ceff00] focus:ring-[#ceff00] focus:ring-offset-0"
                />
                <span className="text-sm">Tenho epicondilite (cotovelo de tenista)</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium mb-3">Preferencia de peso (opcional)</label>
              <div className="flex flex-wrap gap-2">
                {(['heavy', 'standard', 'light', 'no_preference'] as const).map((weight) => (
                  <button
                    key={weight}
                    onClick={() =>
                      setWizardState((prev) => ({ ...prev, weight_preference: weight }))
                    }
                    className={`px-4 py-2 rounded-full border transition-colors ${
                      wizardState.weight_preference === weight
                        ? 'border-[#ceff00] bg-[#ceff00]/10 text-[#ceff00]'
                        : 'border-[#222222] text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    {weight === 'heavy' && 'Pesada'}
                    {weight === 'standard' && 'Padrao'}
                    {weight === 'light' && 'Leve'}
                    {weight === 'no_preference' && 'Sem preferencia'}
                  </button>
                ))}
              </div>
            </div>

            {networkError && (
              <p className="text-red-400 text-sm mt-2">{networkError}</p>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 px-4 py-3 rounded-lg border border-[#222222] text-gray-400 hover:text-white transition-colors"
              >
                Voltar
              </button>
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className="flex-1 bg-[#ceff00] text-black font-semibold px-6 py-3 rounded-lg disabled:opacity-40 hover:bg-[#b8e600] transition-colors"
              >
                {isLoading ? 'Buscando...' : 'Ver Recomendacoes'}
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {step !== 'result' && isLoading && (
          <div className="mt-8">
            <p className="text-sm text-gray-400 mb-4">Analisando seu perfil...</p>
            {renderSkeletons()}
          </div>
        )}

        {/* Result State */}
        {step === 'result' && result && (
          <div className="space-y-6">
            {renderCards(result.recommendations)}

            {/* Chat Panel */}
            {messages.length > 0 && (
              <section className="mt-8 border border-[#222222] rounded-xl bg-[#111111] max-h-[400px] flex flex-col">
                <div className="p-4 border-b border-[#222222] flex items-center gap-2">
                  <span className="text-sm font-semibold">Consultor IA</span>
                </div>
                <div
                  ref={chatScrollRef}
                  className="flex-1 overflow-y-auto p-4 space-y-4"
                >
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={
                        msg.role === 'assistant'
                          ? 'text-sm text-gray-300'
                          : 'text-sm text-white text-right'
                      }
                    >
                      <div
                        className={
                          msg.role === 'assistant'
                            ? 'bg-[#1a1a1a] rounded-lg p-3 inline-block max-w-[85%]'
                            : 'bg-[#ceff00]/20 rounded-lg p-3 inline-block max-w-[85%] ml-auto'
                        }
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {isChatLoading && (
                    <div className="text-sm text-gray-500 animate-pulse">Pensando...</div>
                  )}
                </div>
                <form
                  onSubmit={handleChatSubmit}
                  className="p-3 border-t border-[#222222] flex gap-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Pergunte sobre as raquetes..."
                    className="flex-1 bg-[#0a0a0a] border border-[#222222] rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#ceff00]"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isChatLoading}
                    className="bg-[#ceff00] text-black px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-40"
                  >
                    Enviar
                  </button>
                </form>
              </section>
            )}
          </div>
        )}
      </div>
    </main>
  );
}