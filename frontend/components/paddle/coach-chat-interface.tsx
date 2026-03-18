'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { chatWithCoach, ChatMessage } from '@/lib/api';

interface CoachChatInterfaceProps {
    grokDossier: string;
    contextString: string;
    paddleId?: string;
}

export function CoachChatInterface({ grokDossier, contextString, paddleId }: CoachChatInterfaceProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

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
                            {/* Make bold text actually bold and add paragraphs */}
                            {msg.content.split('\n').map((paragraph, i) => (
                                <p key={i} className={i > 0 ? 'mt-2' : ''}>
                                    {paragraph.split('**').map((text, j) =>
                                        j % 2 === 1 ? <strong key={j} className="text-white font-bold">{text}</strong> : text
                                    )}
                                </p>
                            ))}
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
