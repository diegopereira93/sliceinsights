import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

class LLMService:
    """Service for interacting with Grok (xAI) via the OpenAI SDK wrapper."""
    
    def __init__(self):
        self.api_key = settings.grok_api_key
        # Grok uses the xAI API base url
        self.base_url = "https://api.x.ai/v1"
        self.model_name = "grok-2-latest" # O mais recomendado
        
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            logger.warning("No GROK_API_KEY found. LLM features will be disabled or mocked.")

    async def generate_dossier(self, user_profile: Dict[str, Any], top_paddles: List[Dict[str, Any]]) -> str:
        """
        Generates a personalized dossier explaining why the recommended paddles fit the user.
        """
        if not self.client:
            return "O treinador identificou que essas raquetes são as melhores do mercado para o seu perfil técnico."
        
        system_prompt = """
        Você é um Treinador de Pickleball Profissional e Influente.
        Seu papel é analisar o perfil do aluno e as raquetes recomendadas pelo nosso sistema matemático, 
        e escrever um dossiê curto e persuasivo recomendando essas raquetes. 
        Seja direto, técnico mas amigável.
        """
        
        user_prompt = f"""
        Perfil do Aluno: {user_profile}
        Raquetes Filtradas: {top_paddles}
        
        Escreva um dossiê (2-3 parágrafos) de recomendação para o aluno.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error calling Grok API", error=str(e))
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
