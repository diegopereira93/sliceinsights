'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
    ChevronRight,
    ChevronLeft,
    Target,
    Zap,
    ShieldCheck,
    Trophy,
    Loader2,
    RotateCcw,
    Weight,
    Wallet,
    Heart,
    Users,
    CalendarClock,
    GripHorizontal,
    Activity
} from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import { Paddle } from './paddle-card';
import { getRecommendations, RecommendationRequest } from '@/lib/api';

interface QuizStep {
    key: string;
    title: string;
    question: string;
    type?: 'options' | 'slider';
    minLabel?: string;
    maxLabel?: string;
    options: {
        label: string;
        value: string;
        icon?: React.ReactNode;
        description: string;
    }[];
}

const steps: QuizStep[] = [
    // 1. Nível (skill_level) - Fundamental
    {
        key: 'skill_level',
        title: 'Nível',
        question: 'Qual seu nível de habilidade no Pickleball?',
        options: [
            {
                label: 'Iniciante (3.0 ou menos)',
                value: 'beginner',
                icon: <Target className="w-5 h-5 text-primary-text" />,
                description: 'Aprendendo os fundamentos.'
            },
            {
                label: 'Intermediário (3.5 - 4.0)',
                value: 'intermediate',
                icon: <ShieldCheck className="w-5 h-5 text-primary-text" />,
                description: 'Jogo consistente, evoluindo.'
            },
            {
                label: 'Avançado (4.5+)',
                value: 'advanced',
                icon: <Trophy className="w-5 h-5 text-primary-text" />,
                description: 'Jogador competitivo e experiente.'
            },
        ],
    },
    // 2. Esporte Prévio (Contexto)
    {
        key: 'previous_sport',
        title: 'Background',
        question: 'Você vem de algum outro esporte de raquete?',
        options: [
            {
                label: 'Tênis',
                value: 'tennis',
                icon: <Activity className="w-5 h-5 text-primary-text" />,
                description: 'Acostumado com cordas e swing longo.'
            },
            {
                label: 'Beach Tennis / Padel',
                value: 'beach',
                icon: <Zap className="w-5 h-5 text-primary-text" />,
                description: 'Jogo rápido e voleios.'
            },
            {
                label: 'Ping Pong / Squash',
                value: 'table',
                icon: <Target className="w-5 h-5 text-primary-text" />,
                description: 'Reflexos rápidos e pulso.'
            },
            {
                label: 'Nenhum / Outros',
                value: 'none',
                icon: <Users className="w-5 h-5 text-primary-text" />,
                description: 'Começando do zero no Pickleball.'
            },
        ],
    },
    // 3. Singles vs Doubles (Contexto)
    {
        key: 'format_preference',
        title: 'Formato',
        question: 'Você joga mais Simples ou Duplas?',
        options: [
            {
                label: 'Principalmente Duplas',
                value: 'doubles',
                icon: <Users className="w-5 h-5 text-primary-text" />,
                description: 'Foco em dinks e jogo na rede.'
            },
            {
                label: 'Principalmente Simples',
                value: 'singles',
                icon: <Activity className="w-5 h-5 text-primary-text" />,
                description: 'Cobertura de quadra e drives.'
            },
            {
                label: 'Ambos igualmente',
                value: 'mixed',
                icon: <ShieldCheck className="w-5 h-5 text-primary-text" />,
                description: 'Preciso de versatilidade.'
            },
        ],
    },
    // 4. Foco Principal (play_style)
    {
        key: 'play_style_mix',
        title: 'Estilo de Jogo',
        question: 'Qual seu equilíbrio ideal entre Controle e Potência?',
        type: 'slider',
        minLabel: '100% Controle',
        maxLabel: '100% Power',
        options: [],
    },
    // 5. Spin
    {
        key: 'spin_value',
        title: 'Spin',
        question: 'Quanto você valoriza o spin (efeito) na bola?',
        options: [
            {
                label: 'Muito importante',
                value: 'high',
                icon: <RotateCcw className="w-5 h-5 text-primary-text" />,
                description: 'Uso spin para controlar e atacar.'
            },
            {
                label: 'Razoavelmente',
                value: 'medium',
                icon: <RotateCcw className="w-5 h-5 text-primary-text" />,
                description: 'Spin é útil, mas não essencial.'
            },
            {
                label: 'Não me importo',
                value: 'low',
                icon: <RotateCcw className="w-5 h-5 text-primary-text" />,
                description: 'Prefiro bater chapado.'
            },
        ],
    },
    // 6. Peso
    {
        key: 'weight_preference',
        title: 'Peso',
        question: 'Qual sua preferência de peso da raquete?',
        options: [
            {
                label: 'Mais leve (< 7.8oz)',
                value: 'light',
                icon: <Weight className="w-5 h-5 text-primary-text" />,
                description: 'Mãos rápidas na rede.'
            },
            {
                label: 'Padrão (7.8 - 8.2oz)',
                value: 'standard',
                icon: <Weight className="w-5 h-5 text-primary-text" />,
                description: 'Melhor equilíbrio.'
            },
            {
                label: 'Mais pesada (> 8.2oz)',
                value: 'heavy',
                icon: <Weight className="w-5 h-5 text-primary-text" />,
                description: 'Estabilidade e power.'
            },
        ],
    },
    // 7. Cabo (Grip)
    {
        key: 'handle_preference',
        title: 'Cabo',
        question: 'Você prefere cabo longo ou curto?',
        options: [
            {
                label: 'Longo (Backhand Two-Handed)',
                value: 'long',
                icon: <GripHorizontal className="w-5 h-5 text-primary-text" />,
                description: 'Para quem usa duas mãos.'
            },
            {
                label: 'Padrão / Curto',
                value: 'standard',
                icon: <GripHorizontal className="w-5 h-5 text-primary-text" />,
                description: 'Dedo no paddle ou one-handed.'
            },
            {
                label: 'Sem preferência',
                value: 'any',
                icon: <Target className="w-5 h-5 text-primary-text" />,
                description: 'Me adapto ao que for melhor.'
            },
        ],
    },
    // 8. Frequência
    {
        key: 'frequency',
        title: 'Frequência',
        question: 'Com que frequência você joga?',
        options: [
            {
                label: 'Viciado (4+ vezes/semana)',
                value: 'high',
                icon: <CalendarClock className="w-5 h-5 text-primary-text" />,
                description: 'Preciso de durabilidade máxima.'
            },
            {
                label: 'Regular (1-3 vezes/semana)',
                value: 'medium',
                icon: <CalendarClock className="w-5 h-5 text-primary-text" />,
                description: 'Hobby sério.'
            },
            {
                label: 'Ocasional',
                value: 'low',
                icon: <Activity className="w-5 h-5 text-primary-text" />,
                description: 'Lazer aos finais de semana.'
            },
        ],
    },
    // 9. Conforto / Tennis Elbow (has_tennis_elbow)
    {
        key: 'has_tennis_elbow',
        title: 'Conforto',
        question: 'Você tem dor no cotovelo ou sensibilidade?',
        options: [
            {
                label: 'Sim, tenho Tennis Elbow',
                value: 'true',
                icon: <Heart className="w-5 h-5 text-primary-text" />,
                description: 'Prioridade máxima é conforto/vibração.'
            },
            {
                label: 'Não, estou 100%',
                value: 'false',
                icon: <Zap className="w-5 h-5 text-primary-text" />,
                description: 'Posso focar em performance pura.'
            },
        ],
    },
    // 10. Orçamento (budget_max_brl)
    {
        key: 'budget',
        title: 'Investimento',
        question: 'Quanto você pretende investir?',
        options: [
            {
                label: 'Até R$ 800',
                value: '800',
                icon: <Wallet className="w-5 h-5 text-primary-text" />,
                description: 'Bom para começar.'
            },
            {
                label: 'Até R$ 1.600',
                value: '1600',
                icon: <Wallet className="w-5 h-5 text-primary-text" />,
                description: 'Nível intermediário/avançado.'
            },
            {
                label: 'Sem limite / Premium',
                value: '3000',
                icon: <Trophy className="w-5 h-5 text-primary-text" />,
                description: 'Quero tecnologia de ponta.'
            },
        ],
    },
];

interface RacketFinderQuizProps {
    paddles: Paddle[];
    onRecommend: (paddle: Paddle) => void;
}

interface QuizOptionProps {
    label: string;
    value: string;
    description: string;
    icon: React.ReactNode;
    selected: boolean;
    onClick: () => void;
}

function QuizOption({ label, value, description, icon, selected, onClick }: QuizOptionProps) {
    return (
        <Button
            variant="secondary"
            className={cn(
                "w-full h-auto p-4 flex items-center justify-start gap-4 border-2 transition-all backdrop-blur-md group",
                selected ? 'border-primary bg-primary/20' : 'border-white/5 bg-white/5 hover:border-white/10'
            )}
            data-option={value}
            onClick={onClick}
        >
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 transition-transform group-hover:scale-110">
                {icon}
            </div>
            <div className="text-left">
                <div className="font-bold text-white">{label}</div>
                <div className="text-xs text-zinc-400">{description}</div>
            </div>
            <ChevronRight className={cn("ml-auto w-4 h-4 text-zinc-500 transition-transform", selected ? "translate-x-1 text-primary" : "group-hover:translate-x-1")} />
        </Button>
    );
}

// Maps 10 quiz answers to backend parameters
function mapAnswersToRequest(answers: Record<string, string>): RecommendationRequest {
    // Derive play_style from help_with (Q4)
    let play_style: 'POWER' | 'CONTROL' | 'BALANCED' = 'BALANCED';

    if (answers.help_with === 'offense') {
        play_style = 'POWER';
    } else if (answers.help_with === 'soft_game') {
        play_style = 'CONTROL';
    } else if (answers.help_with === 'defense') {
        play_style = 'CONTROL'; // Defense usually implies control/block
    }

    // Adjust play style based on Singles/Doubles if it's 'mixed' or 'everything'
    if (play_style === 'BALANCED' && answers.format_preference === 'singles') {
        play_style = 'POWER'; // Singles leans slightly more to power
    }

    // Map skill_level
    const skill_map: Record<string, 'beginner' | 'intermediate' | 'advanced'> = {
        'beginner': 'beginner',
        'intermediate': 'intermediate',
        'advanced': 'advanced',
    };

    const budget = parseFloat(answers.budget) || 3000;

    // Parse slider value if present
    const powerMix = answers.play_style_mix ? parseInt(answers.play_style_mix) : undefined;

    return {
        skill_level: skill_map[answers.skill_level] || 'intermediate',
        play_style: powerMix !== undefined ? 'balanced' : play_style.toLowerCase(),
        has_tennis_elbow: answers.has_tennis_elbow === 'true',
        budget_max_brl: budget,
        spin_preference: (answers.spin_value === 'high' || answers.spin_value === 'medium') ? answers.spin_value : undefined,
        weight_preference: (answers.weight_preference === 'light' || answers.weight_preference === 'heavy') ? answers.weight_preference : undefined,
        power_preference_percent: powerMix,
        limit: 1
    };
}

export function RacketFinderQuiz({ paddles, onRecommend }: RacketFinderQuizProps) {
    const [currentStep, setCurrentStep] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [isRecommending, setIsRecommending] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [recommendedPaddle, setRecommendedPaddle] = useState<Paddle | null>(null);

    const [loadingLabel, setLoadingLabel] = useState('Analisando seu perfil...');

    const loadingLabels = [
        'Analisando seu perfil...',
        'Processando respostas...',
        'Comparando specs técnicas...',
        'Calculando match score...',
        'Buscando ofertas no mercado...',
        'Quase lá...'
    ];

    const handleSelect = (value: string) => {
        const newAnswers = { ...answers, [steps[currentStep].key]: value };
        setAnswers(newAnswers);

        if (currentStep < steps.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            findRecommendation(newAnswers);
        }
    };

    const findRecommendation = async (finalAnswers: Record<string, string>) => {
        setIsRecommending(true);

        // Start rotating labels
        let labelIndex = 0;
        const interval = setInterval(() => {
            labelIndex = (labelIndex + 1) % loadingLabels.length;
            setLoadingLabel(loadingLabels[labelIndex]);
        }, 350);

        try {
            const request = mapAnswersToRequest(finalAnswers);

            // Multi-tasking: get data and wait at least 1.8s for "Labor Illusion" (longer for 10 questions)
            const [result] = await Promise.all([
                getRecommendations(request),
                new Promise(resolve => setTimeout(resolve, 1800))
            ]);

            clearInterval(interval);

            if (result.recommendations && result.recommendations.length > 0) {
                const rec = result.recommendations[0];

                // --- Persist for Hyper-Personalization ---
                if (typeof window !== 'undefined') {
                    const profileData = JSON.stringify({
                        answers: finalAnswers,
                        request: request,
                        timestamp: new Date().toISOString()
                    });
                    sessionStorage.setItem('slice_quiz_results', profileData);
                    localStorage.setItem('user_profile', profileData);
                }

                // Try to find the paddle in our current list or just use what backend gave us
                const localPaddle = paddles.find(p => p.id === rec.paddle_id);
                if (localPaddle) {
                    onRecommend({
                        ...localPaddle,
                        matchReasons: rec.match_reasons,
                        tags: rec.tags
                    });
                    setRecommendedPaddle(localPaddle);
                } else {
                    // Fallback to minimal paddle object if not found in current pre-loaded list
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
            // Fallback to local logic if API fails
            onRecommend(paddles[0]);
        } finally {
            setIsRecommending(false);
            setShowResults(true);
        }
    };

    // Progress calculation for 10 steps
    const progress = ((currentStep + 1) / steps.length) * 100;

    return (
        <div className="w-full max-w-md mx-auto">
            {/* Progress bar */}
            <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-medium text-zinc-400">
                        Pergunta {currentStep + 1} de {steps.length}
                    </span>
                    <span className="text-xs font-bold text-primary-text">
                        {Math.round(progress)}%
                    </span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-primary rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.3 }}
                    />
                </div>
            </div>

            <AnimatePresence mode="wait">
                <motion.div
                    key={isRecommending ? 'loading' : currentStep}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                >
                    {isRecommending ? (
                        <div className="py-12 flex flex-col items-center justify-center gap-4">
                            <Loader2 className="w-10 h-10 animate-spin text-primary-text" />
                            <p className="font-bold text-lg min-h-[1.5em] transition-all duration-300">{loadingLabel}</p>
                        </div>
                    ) : showResults ? (
                        <div className="py-8 flex flex-col items-center justify-center text-center gap-4">
                            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mb-2">
                                <Zap className="w-8 h-8 text-primary-text shadow-glow" />
                            </div>
                            <h2 className="text-2xl font-bold">Match Perfeito Encontrado!</h2>
                            <p className="text-zinc-400 max-w-[280px] mb-2">Preparamos uma recomendação personalizada baseada no seu perfil.</p>

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

                            <div className="flex flex-col gap-2 w-full">
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
                                        setCurrentStep(0);
                                        setAnswers({});
                                        setRecommendedPaddle(null);
                                    }}
                                    variant="ghost"
                                    className="text-xs text-zinc-500 hover:text-zinc-300"
                                >
                                    Refazer Quiz
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="mb-6 text-center">
                                <h3 className="text-sm font-medium text-primary-text mb-1 uppercase tracking-wider">{steps[currentStep].title}</h3>
                                <h2 className="text-xl font-bold">{steps[currentStep].question}</h2>
                            </div>

                            <div className="space-y-3">
                                {steps[currentStep].type === 'slider' ? (
                                    <div className="py-8 px-4 flex flex-col gap-6">
                                        <div className="flex justify-between font-bold text-sm">
                                            <span className="text-blue-400">{steps[currentStep].minLabel}</span>
                                            <span className="text-red-400">{steps[currentStep].maxLabel}</span>
                                        </div>
                                        <Slider
                                            defaultValue={[50]}
                                            max={100}
                                            step={1}
                                            className="w-full"
                                            value={[parseInt(answers[steps[currentStep].key] || '50')]}
                                            onValueChange={(vals) => {
                                                setAnswers({ ...answers, [steps[currentStep].key]: vals[0].toString() });
                                            }}
                                        />
                                        <div className="text-center font-mono text-xl">
                                            {answers[steps[currentStep].key] || '50'}% Power
                                        </div>
                                        <div className="text-center text-xs text-zinc-400">
                                            Arraste para definir sua preferência.
                                        </div>
                                        <Button
                                            onClick={() => {
                                                if (!answers[steps[currentStep].key]) {
                                                    // Set default if not touched
                                                    handleSelect('50');
                                                } else {
                                                    // Move next
                                                    handleSelect(answers[steps[currentStep].key]);
                                                }
                                            }}
                                            className="w-full mt-4"
                                        >
                                            Confirmar
                                        </Button>
                                    </div>
                                ) : (
                                    steps[currentStep].options.map((option) => (
                                        <QuizOption
                                            key={option.value}
                                            label={option.label}
                                            value={option.value}
                                            description={option.description}
                                            icon={option.icon}
                                            selected={answers[steps[currentStep].key] === option.value}
                                            onClick={() => handleSelect(option.value)}
                                        />
                                    ))
                                )}
                            </div>
                        </>
                    )}
                </motion.div>
            </AnimatePresence>

            {currentStep > 0 && !isRecommending && !showResults && (
                <Button
                    variant="ghost"
                    size="sm"
                    className="mt-6 text-white/60 hover:text-white hover:bg-white/10"
                    onClick={() => setCurrentStep(currentStep - 1)}
                >
                    <ChevronLeft className="w-4 h-4 mr-1" /> Voltar
                </Button>
            )}
        </div>
    );
}
