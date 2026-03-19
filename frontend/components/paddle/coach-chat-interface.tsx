'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { chatWithCoach, ChatMessage } from '@/lib/api';
import { Paddle } from '@/types/paddle';

interface CoachChatInterfaceProps {
    grokDossier: string;
    contextString: string;
    paddleId?: string;
    paddles?: Paddle[];
    onPaddleClick?: (paddle: Paddle) => void;
}

export function CoachChatInterface({ grokDossier, contextString, paddleId, paddles = [], onPaddleClick }: CoachChatInterfaceProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Function to find paddle in the list and return it
    const findPaddleByName = (text: string): Paddle | null => {
        if (!paddles) return null;
        return paddles.find(p => {
            const fullName = `${p.brand} ${p.name}`;
            return text.toLowerCase().includes(fullName.toLowerCase()) ||
                   text.toLowerCase().includes(p.name.toLowerCase());
        }) || null;
    };

    // Function to parse message content and create links for paddle names
    const renderMessageWithLinks = (content: string) => {
        // Split by newlines
        return content.split('\n').map((paragraph, paraIdx) => {
            // Process paragraph for bold text and paddle links
            const parts = paragraph.split(/(\*\*[^*]+\*\*)/g);

            const processedParts = parts.map((part, partIdx) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                    // Bold text
                    const boldText = part.slice(2, -2);
                    return <strong key={partIdx} className="text-white font-bold">{boldText}</strong>;
                }

                // Check for paddle names in this part
                const words = part.split(/(\s+)/);
                const nodes = [];

                for (let i = 0; i < words.length; i += 2) {
                    const word = words[i];
                    const space = words[i + 1] || '';

                    // Try to find paddle by this word and next word combined
                    let paddle = findPaddleByName(word);
                    let textToUse = word;

                    if (!paddle && i + 2 < words.length) {
                        textToUse = `${word} ${words[i + 2]}`;
                        paddle = findPaddleByName(textToUse);
                        if (paddle) {
                            nodes.push(
                                <button
                                    key={`${partIdx}-${nodes.length}`}
                                    onClick={() => paddle && onPaddleClick?.(paddle)}
                                    className="text-primary hover:text-primary/80 underline cursor-pointer transition-colors font-semibold"
                                    title={`R$ ${paddle.price}`}
                                >
                                    {textToUse}
                                </button>
                            );
                            nodes.push(space);
                            nodes.push(words[i + 3] || '');
                            i += 2;
                            continue;
                        }
                    }

                    if (paddle) {
                        nodes.push(
                            <button
                                key={`${partIdx}-${nodes.length}`}
                                onClick={() => paddle && onPaddleClick?.(paddle)}
                                className="text-primary hover:text-primary/80 underline cursor-pointer transition-colors font-semibold"
                                title={`R$ ${paddle.price}`}
                            >
                                {word}
                            </button>
                        );
                    } else {
                        nodes.push(word);
                    }
                    nodes.push(space);
                }

                return nodes;
            });

            return (
                <p key={paraIdx} className={paraIdx > 0 ? 'mt-2' : ''}>
                    {processedParts}
                </p>
            );
        });
    };

    // Initial Coach Message using the Dossier
    useEffect(() => {
        if (grokDossier && messages.length === 0) {
            setMessages([
                { role: 'assistant', content: grokDossier }
            ]);
        }
    }, [grokDossier]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg: ChatMessage = { role: 'user', content: input.trim() };
        const newMessages = [...messages, userMsg];

        setMessages(newMessages);
        setInput('');
        setIsLoading(true);

        try {
            // Only send the last 6 messages to save context limits, but always include system context
            const historyToSend = newMessages.slice(-6);

            const response = await chatWithCoach(historyToSend, contextString, paddleId);

            if (response && response.reply) {
                setMessages(prev => [...prev, { role: 'assistant', content: response.reply }]);
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Desculpe, meu sistema de inteligência avançada está offline para atualizações neste momento. Podes conferir as especificações da raquete na nossa tabela!'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full mt-8 rounded-2xl bg-white/5 border border-white/10 overflow-hidden flex flex-col shadow-2xl">
            {/* Header */}
            <div className="bg-white/5 border-b border-white/10 p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center shrink-0 border border-primary/30">
                    <Bot className="w-5 h-5 text-primary" />
                </div>
                <div>
                    <h3 className="font-bold text-white text-sm">Treinador xAI</h3>
                    <div className="flex items-center gap-1.5 mt-0.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-bold">Online para Consultoria</span>
                    </div>
                </div>
            </div>

            {/* Chat Area */}
            <div className="p-4 max-h-[350px] overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.map((msg, idx) => (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        key={idx}
                        className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${msg.role === 'user' ? 'bg-zinc-800' : 'bg-primary/20'
                            }`}>
                            {msg.role === 'user' ? <User className="w-4 h-4 text-zinc-400" /> : <Bot className="w-4 h-4 text-primary" />}
                        </div>
                        <div className={`p-3 rounded-2xl text-sm leading-relaxed max-w-[85%] ${msg.role === 'user'
                            ? 'bg-primary text-primary-foreground rounded-tr-sm'
                            : 'bg-white/5 text-zinc-300 rounded-tl-sm border border-white/5'
                            }`}>
                            {/* Render message with paddle links */}
                            {msg.role === 'user' ? (
                                msg.content
                            ) : (
                                renderMessageWithLinks(msg.content)
                            )}
                        </div>
                    </motion.div>
                ))}

                {isLoading && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-primary/20">
                            <Bot className="w-4 h-4 text-primary" />
                        </div>
                        <div className="p-4 rounded-2xl bg-white/5 rounded-tl-sm border border-white/5">
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-3 bg-white/5 border-t border-white/10">
                <form
                    className="flex gap-2 relative"
                    onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                >
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Pergunte sobre as raquetes recomendadas..."
                        className="bg-black/20 border-white/10 text-white placeholder:text-zinc-500 rounded-xl pr-12 focus-visible:ring-primary h-11"
                        disabled={isLoading}
                    />
                    <Button
                        type="submit"
                        size="icon"
                        disabled={!input.trim() || isLoading}
                        className="absolute right-1 top-1 h-9 w-9 rounded-lg"
                    >
                        <Send className="w-4 h-4" />
                    </Button>
                </form>
            </div>
        </div>
    );
}
