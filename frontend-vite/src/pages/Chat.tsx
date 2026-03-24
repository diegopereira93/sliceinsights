import { useState, useRef, useEffect } from "react";
import { useSendChatMessage, ChatMessageInputConversationHistoryItem } from "../lib/api-client";
import { Send, Terminal, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export default function Chat() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessageInputConversationHistoryItem[]>([
    { role: "assistant", content: "Bem-vindo ao Command Center. Sou seu técnico virtual especializado em equipamentos. O que você quer saber sobre raquetes hoje?" }
  ]);
  
  const chatMutation = useSendChatMessage();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    
    // Optimistic UI update
    const newHistory: ChatMessageInputConversationHistoryItem[] = [
      ...history, 
      { role: "user", content: userMessage }
    ];
    setHistory(newHistory);

    try {
      const response = await chatMutation.mutateAsync({
        data: {
          message: userMessage,
          conversationHistory: newHistory.slice(0, -1) // send previous history
        }
      });

      setHistory([...newHistory, { role: "assistant", content: response.reply }]);
    } catch (error) {
      setHistory([...newHistory, { role: "assistant", content: "[ERRO DE CONEXÃO: Tente novamente mais tarde]" }]);
    }
  };

  return (
    <div className="h-screen flex flex-col pt-4 pb-[80px]">
      {/* Top Bar - Command Center Vibe */}
      <div className="px-4 py-3 mx-4 glass-panel rounded-2xl flex items-center justify-between mb-4 border-primary/20 bg-zinc-950/90 z-10">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-full overflow-hidden border border-primary/50 shadow-[0_0_10px_rgba(163,230,53,0.2)]">
            <img src={`${import.meta.env.BASE_URL}images/ai-avatar.png`} alt="AI Coach" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-primary/20 mix-blend-overlay" />
          </div>
          <div>
            <h2 className="text-white font-bold font-display tracking-wide uppercase flex items-center gap-2">
              NEXUS-7 <Cpu className="w-4 h-4 text-primary" />
            </h2>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] text-primary font-mono tracking-widest">ONLINE PARA CONSULTORIA</span>
            </div>
          </div>
        </div>
        <div className="hidden md:flex text-xs font-mono text-zinc-500 gap-4">
          <span>DATABANK: <span className="text-zinc-300">CONNECTED</span></span>
          <span>LATENCY: <span className="text-primary">12ms</span></span>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 custom-scrollbar">
        <div className="max-w-3xl mx-auto space-y-6 pb-4">
          {history.map((msg, idx) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={idx} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[85%] rounded-2xl p-4 ${
                msg.role === 'user' 
                  ? 'bg-primary text-black rounded-tr-sm' 
                  : 'bg-zinc-900 border border-white/10 text-zinc-100 rounded-tl-sm shadow-[0_0_15px_rgba(0,0,0,0.5)]'
              }`}>
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2 text-primary">
                    <Terminal className="w-3 h-3" />
                    <span className="text-[10px] font-mono tracking-wider">SYSTEM.RESPONSE</span>
                  </div>
                )}
                <p className="leading-relaxed whitespace-pre-wrap font-medium">{msg.content}</p>
              </div>
            </motion.div>
          ))}
          {chatMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-zinc-900 border border-white/10 rounded-2xl rounded-tl-sm p-4 flex gap-1">
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="px-4 py-2 mt-auto">
        <div className="max-w-3xl mx-auto relative">
          <form onSubmit={handleSend} className="relative">
            <input 
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Pergunte sobre as raquetes recomendadas..."
              className="w-full bg-zinc-900/80 backdrop-blur-md border border-white/10 rounded-2xl py-4 pl-4 pr-14 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-lg"
              disabled={chatMutation.isPending}
            />
            <button 
              type="submit" 
              disabled={!input.trim() || chatMutation.isPending}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-primary text-black rounded-xl hover:bg-white transition-colors disabled:opacity-50 disabled:hover:bg-primary"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[10px] font-mono text-zinc-600">ENCRYPTED END-TO-END CONNECTION</span>
          </div>
        </div>
      </div>
    </div>
  );
}
