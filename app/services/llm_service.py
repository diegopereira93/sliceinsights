import logging
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

class LLMService:
    """Service for interacting with Groq API (Llama 3.3)."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model_name = "llama-3.3-70b-versatile" # O mesmo modelo do lakehouse
        
        self.client = None
        if self.api_key:
            self.client = AsyncGroq(
                api_key=self.api_key,
            )
        else:
            logger.warning("No GROQ_API_KEY found. LLM features will be disabled or mocked.")

    async def generate_dossier(self, user_profile: Dict[str, Any], top_paddles: List[Dict[str, Any]]) -> str:
        """
        Generates a personalized dossier explaining why the recommended paddles fit the user.
        Uses Structured Context Injection (SCI) for data-grounded responses.
        """
        if not self.client:
            return "O treinador identificou que essas raquetes são as melhores do mercado para o seu perfil técnico."
        
        system_prompt = """Você é um Treinador de Pickleball Profissional e Influente.

DADOS ESTRUTURADOS fornecidos:
- Perfil do Aluno: nível, estilo de jogo, orçamento, restrições físicas
- Raquetes Filtradas: specs técnicos (core, face material, spin RPM, swing weight),
  ratings calculados (power/control/spin/sweet_spot em escala 0-10),
  custo-benefício (value_score), e preço em R$

REGRAS:
1. Use os RATINGS NUMÉRICOS para justificar suas escolhas (ex: "Power 9/10 é ideal para drives agressivos")
2. Cite SPECS REAIS quando relevante (ex: "Core de 16mm absorve vibração para quem tem epicondilite")
3. Compare as raquetes entre si usando os dados (ex: "A Raquete A tem Spin RPM 280 vs 240 da B")
4. Se value_score existir, mencione custo-benefício
5. Mantenha o tom direto, técnico e amigável (2-3 parágrafos)
6. NUNCA invente dados que não foram fornecidos — use apenas o que está no contexto"""
        
        user_prompt = f"""Perfil do Aluno: {user_profile}

Raquetes Filtradas (com specs e ratings):
{top_paddles}

Escreva um dossiê personalizado (2-3 parágrafos) recomendando essas raquetes para o aluno,
citando dados numéricos e specs reais para fundamentar cada escolha."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error calling Groq API for dossier", error=str(e))
            return "Nossa IA encontrou um gargalo temporário, mas as sugestões acima foram rigorosamente filtradas para você."
            
    async def chat_with_context(self, chat_history: List[Dict[str, str]], context: str) -> str:
        """
        Interacts with the user within the strict context of the recommended paddles (RAG).
        """
        if not self.client:
            return "Chat indisponível no momento."
            
        system_prompt = f"""
        Você é o Consultor Técnico de Raquetes deste sistema.
        O usuário já recebeu sua recomendação. Responda as dúvidas dele APENAS sobre as raquetes recomendadas ou conceitos de Pickleball.
        
        CONTEXTO RELEVANTE: 
        {context}
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error in Coach Chatbot (Grok API)", error=str(e))
            return "Desculpe, meu cérebro digital falhou por um instante. Pode repetir a pergunta?"

# Singleton
llm_service = LLMService()
