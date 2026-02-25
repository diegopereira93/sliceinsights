'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
    Target,
    Zap,
    Trophy,
    Loader2,
    Send,
    MessageSquare
} from 'lucide-react';
import { Paddle } from './paddle-card';
import { getConversationalRecommendations, captureLead } from '@/lib/api';
import { CoachChatInterface } from './coach-chat-interface';

interface RacketFinderQuizProps {
    paddles: Paddle[];
    onRecommend: (paddle: Paddle) => void;
}

export function RacketFinderQuiz({ paddles, onRecommend }: RacketFinderQuizProps) {
    const [userQuery, setUserQuery] = useState('');
    const [isRecommending, setIsRecommending] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [recommendedPaddle, setRecommendedPaddle] = useState<Paddle | null>(null);
    const [grokDossier, setGrokDossier] = useState<string>('');
    const [isLeadGate, setIsLeadGate] = useState(false);
    const [leadName, setLeadName] = useState('');
    const [leadEmail, setLeadEmail] = useState('');
    const [isSubmittingLead, setIsSubmittingLead] = useState(false);

    const [loadingLabel, setLoadingLabel] = useState('Interpretando sua jogabilidade...');

    const loadingLabels = [
        'Interpretando sua jogabilidade...',
        'Traduzindo sua fala para o banco de dados...',
        'Buscando as raquetes perfeitas...',
        'Calculando física estrutural...',
        'O Treinador está escrevendo seu dossiê...',
        'Quase lá...'
    ];

    const handleSubmitQuery = (e: React.FormEvent) => {
        e.preventDefault();
        if (!userQuery.trim()) return;
        setIsLeadGate(true);
    };

    const handleLeadSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!leadEmail) return;
        setIsSubmittingLead(true);
        try {
            await captureLead(leadEmail, leadName);
        } catch (error) {
            console.error('Failed to capture lead:', error);
        } finally {
            setIsSubmittingLead(false);
            setIsLeadGate(false);
            findRecommendation(userQuery); // Resume flow
        }
    };

    const findRecommendation = async (query: string) => {
        setIsRecommending(true);

        // Start rotating labels
        let labelIndex = 0;
        const interval = setInterval(() => {
            labelIndex = (labelIndex + 1) % loadingLabels.length;
            setLoadingLabel(loadingLabels[labelIndex]);
        }, 1500);

        try {
            const request = { user_query: query, limit: 1 };

            // Multi-tasking: get data and wait at least 3s for "Labor Illusion"
            const [result] = await Promise.all([
                getConversationalRecommendations(request),
                new Promise(resolve => setTimeout(resolve, 3000))
            ]);

            clearInterval(interval);

            if (result.recommendations && result.recommendations.length > 0) {
                const rec = result.recommendations[0];

                if (result.grok_dossier) {
                    setGrokDossier(result.grok_dossier);
                }

                if (typeof window !== 'undefined') {
                    const profileData = JSON.stringify({
                        user_query: query,
                        request: request,
                        timestamp: new Date().toISOString()
                    });
                    sessionStorage.setItem('slice_quiz_results', profileData);
                    localStorage.setItem('user_profile', profileData);
                }

                const localPaddle = paddles.find(p => p.id === rec.paddle_id);
                if (localPaddle) {
                    onRecommend({
                        ...localPaddle,
                        matchReasons: rec.match_reasons,
                        tags: rec.tags
                    });
                    setRecommendedPaddle(localPaddle);
                } else {
                    const fallbackPaddle: Paddle = {
                        id: rec.paddle_id,
                        name: rec.model_name,
                        brand: rec.brand_name,
                        price: rec.min_price_brl || 0,
                        image: `https://placehold.co/400x533/png?text=${encodeURIComponent(rec.model_name)}`,
                        rating: 4.5,
                        weight: 'N/A',
                        surfaceMaterial: 'N/A',
                        powerLevel: 'Medium',
                        controlLevel: 'Medium',
                        power: 5,
                        control: 5,
                        spin: 5,
                        sweetSpot: 5,
                        matchReasons: rec.match_reasons,
                        tags: rec.tags
                    };
                    onRecommend(fallbackPaddle);
                    setRecommendedPaddle(fallbackPaddle);
                }
            }
        } catch (error) {
            console.error('Failed to get recommendation:', error);
            onRecommend(paddles[0]);
        } finally {
            setIsRecommending(false);
            setShowResults(true);
        }
    };

    return (
        <div className="w-full max-w-md mx-auto">
            <AnimatePresence mode="wait">
                <motion.div
                    key={isLeadGate ? 'lead' : isRecommending ? 'loading' : showResults ? 'results' : 'input'}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                >
                    {isLeadGate ? (
                        <div className="py-8 flex flex-col items-center justify-center text-center gap-4">
                            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mb-4">
                                <Trophy className="w-8 h-8 text-primary shadow-glow" />
                            </div>
                            <h2 className="text-2xl font-bold">Quase lá!</h2>
                            <p className="text-zinc-400 mb-6">
                                O Treinador já entendeu o seu jogo. Para qual e-mail devo enviar o seu Dossiê Completo de Recomendação?
                            </p>
                            <form onSubmit={handleLeadSubmit} className="w-full flex flex-col gap-3">
                                <input
                                    type="text"
                                    placeholder="Seu nome"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary"
                                    value={leadName}
                                    onChange={(e) => setLeadName(e.target.value)}
                                    required
                                />
                                <input
                                    type="email"
                                    placeholder="Seu melhor e-mail"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary"
                                    value={leadEmail}
                                    onChange={(e) => setLeadEmail(e.target.value)}
                                    required
                                />
                                <Button
                                    type="submit"
                                    disabled={isSubmittingLead || !leadEmail}
                                    className="w-full h-12 font-bold mt-2 rounded-xl"
                                >
                                    {isSubmittingLead ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Ver Minha Recomendação'}
                                </Button>
                            </form>
                        </div>
                    ) : isRecommending ? (
                        <div className="py-12 flex flex-col items-center justify-center gap-4">
                            <Loader2 className="w-10 h-10 animate-spin text-primary-text" />
                            <p className="font-bold text-lg min-h-[1.5em] text-center transition-all duration-300">{loadingLabel}</p>
                        </div>
                    ) : showResults ? (
                        <div className="py-8 flex flex-col items-center justify-center text-center gap-4">
                            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mb-2">
                                <Zap className="w-8 h-8 text-primary-text shadow-glow" />
                            </div>
                            <h2 className="text-2xl font-bold">Match Perfeito Encontrado!</h2>
                            <p className="text-zinc-400 max-w-[280px] mb-2">Baseado no que você me contou, eu faria esta escolha:</p>

                            {recommendedPaddle && (
                                <motion.div
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 flex items-center gap-4 mb-4"
                                >
                                    <div className="w-16 h-16 rounded-xl overflow-hidden bg-muted flex-shrink-0">
                                        <img src={recommendedPaddle.image} alt={recommendedPaddle.name} className="w-full h-full object-cover" />
                                    </div>
                                    <div className="flex-1 text-left min-w-0">
                                        <p className="text-[10px] uppercase font-bold text-primary tracking-wider">{recommendedPaddle.brand}</p>
                                        <p className="font-bold truncate">{recommendedPaddle.name}</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-xs font-mono font-bold text-white">R$ {recommendedPaddle.price}</span>
                                            <div className="h-1 w-1 rounded-full bg-white/20" />
                                            <span className="text-[10px] text-zinc-400">Nota: {recommendedPaddle.rating}</span>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {grokDossier && recommendedPaddle && (
                                <div className="w-full text-left mb-4">
                                    <CoachChatInterface
                                        grokDossier={grokDossier}
                                        contextString={`O usuário recebeu a raquete ${recommendedPaddle.brand} ${recommendedPaddle.name} por R$${recommendedPaddle.price}. Responda dúvidas sobre essa raquete.`}
                                    />
                                </div>
                            )}

                            <div className="flex flex-col gap-2 w-full mt-4">
                                <Button
                                    onClick={() => {
                                        if (recommendedPaddle) onRecommend(recommendedPaddle);
                                        setShowResults(false);
                                    }}
                                    variant="default"
                                    className="w-full font-bold h-12 rounded-xl"
                                >
                                    Ver Detalhes da Raquete
                                </Button>
                                <Button
                                    onClick={() => {
                                        setShowResults(false);
                                        setUserQuery('');
                                        setRecommendedPaddle(null);
                                    }}
                                    variant="ghost"
                                    className="text-xs text-zinc-500 hover:text-zinc-300 mt-2"
                                >
                                    Fazer nova busca
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center gap-6">
                            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mb-2">
                                <MessageSquare className="w-8 h-8 text-primary shadow-glow" />
                            </div>
                            <div className="text-center">
                                <h2 className="text-2xl font-bold mb-2">Qual seu estilo de jogo?</h2>
                                <p className="text-zinc-400 text-sm mb-6">
                                    Esqueça filtros difíceis. Me conte em áudio ou texto: como você joga?
                                    (Ex: Sou intermediário, gosto de atacar o tempo todo e sofro de tennis elbow. Quero gastar no máximo 1500 reais).
                                </p>
                            </div>

                            <form onSubmit={handleSubmitQuery} className="w-full flex flex-col gap-4">
                                <div className="relative">
                                    <textarea
                                        value={userQuery}
                                        onChange={(e) => setUserQuery(e.target.value)}
                                        placeholder="Digite ou cole como você joga..."
                                        className="w-full h-32 bg-white/5 border border-white/10 rounded-2xl p-4 text-white focus:outline-none focus:border-primary resize-none placeholder:text-zinc-600"
                                        required
                                    />
                                    <div className="absolute bottom-4 right-4 flex items-center gap-2">
                                        <p className="text-xs text-zinc-600 hidden sm:block">A IA lerá sua mensagem</p>
                                    </div>
                                </div>
                                <Button
                                    type="submit"
                                    disabled={!userQuery.trim()}
                                    className="w-full h-14 font-bold rounded-xl text-lg flex items-center gap-2 group"
                                >
                                    Descobrir Raquete <Send className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </Button>
                            </form>

                            <div className="mt-8 flex flex-wrap gap-2 justify-center opacity-60">
                                <span className="text-xs bg-white/5 px-2 py-1 rounded-md">"Jogo há 1 ano"</span>
                                <span className="text-xs bg-white/5 px-2 py-1 rounded-md">"Douçada de fundo"</span>
                                <span className="text-xs bg-white/5 px-2 py-1 rounded-md">"Dor no pulso"</span>
                                <span className="text-xs bg-white/5 px-2 py-1 rounded-md">"Até R$800"</span>
                            </div>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
