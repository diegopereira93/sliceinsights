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

    async def parse_query_to_filters(self, user_query: str) -> Dict[str, Any]:
        """
        Translates natural language into a strictly typed JSON dictionary matching the UserProfile schema.
        This provides a safe "Text-to-SQL-Filters" barrier.
        """
        if not self.client:
            # Fallback mock for testing without API Key
            return {
                "skill_level": "Beginner",
                "play_style": "Balanced",
                "has_tennis_elbow": False,
                "budget_max_brl": 1500
            }
            
        system_prompt = """
Você é um analisador avançado de "Text-to-Filter" para uma loja de Pickleball.
Sua única função é extrair parâmetros da mensagem do usuário e retornar EXATAMENTE um objeto JSON.

ESQUEMA DO JSON ESPERADO (não adicione outras chaves):
{
  "skill_level": "Beginner" | "Intermediate" | "Advanced",
  "play_style": "Power" | "Control" | "Balanced",
  "has_tennis_elbow": true | false,
  "budget_max_brl": número | null,
  "weight_preference": "heavy" | "standard" | "light" | "no_preference" | null
}

REGRAS:
- Se o usuário não disser o preço, defina budget_max_brl como null.
- Se falar de lesão no pulso/cotovelo/braço, defina has_tennis_elbow como true.
- Se falar que está começando, é Beginner.
- Se quiser atacar/bater forte: Power. Se quiser defender/pingar: Control.
- Retorne APENAS o JSON válido.
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=200
            )
            import json
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error("Error parsing user query to filters via LLM", error=str(e))
            # Safe Fallback
            return {
                "skill_level": "Beginner",
                "play_style": "Balanced",
                "has_tennis_elbow": False,
                "budget_max_brl": None
            }

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
