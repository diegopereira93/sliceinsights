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
  custo-benefício (value_score), preço em R$, e confiabilidade (specs_confidence)

DIRETRIZES DE RECOMENDAÇÃO (CRÍTICO):
1. Avalie o campo indicador de confiabilidade ("specs_confidence", de 0.0 a 1.0) para ajustar seu tom:
   - Se for ALTO (>= 0.75): Faça uma análise técnica profunda citando as notas de power/control/spin (ex: "Nota 9 em controle").
   - Se for PARCIAL (0.30 a 0.74): NÃO mencione e não invente notas de performance. Foque sua análise na construção da raquete (ex: "Seu núcleo de 16mm de polímero e face em fibra de carbono entregam excelente estabilidade").
   - Se for BAIXO (< 0.30): Foque inteiramente no apelo da marca, no design e em como o modelo se encaixa no orçamento do aluno. Não discuta especificações que você não tem.

REGRAS ANTI-VAZAMENTO (PROIBIDO):
- NUNCA escreva os nomes de variáveis do sistema no seu texto como `specs_confidence`, `value_score`, `has_incomplete_data`, `power_rating`, etc.
- Ao invés de "O value_score é 11", diga: "O custo-benefício desta raquete é excelente".
- Ao invés de justificar suas limitações ("Como a confiança é 0.74 e não tenho dados precisos...", "Apesar dos dados incompletos..."), aja com naturalidade, focando apenas nos dados reais que você possui. O aluno não sabe e não deve saber como você calcula a tabela por trás.
- NUNCA cite formatos de código puro da base, como referências de Enums (ex: nunca diga "A forma é PaddleShape.ELONGATED"). Utilize linguagem natural se o dado aparecer dessa forma.

REGRAS DE CONTEÚDO:
- Compare as opções apenas nos pontos onde há dados para ambas.
- O texto final deve ter 2 a 3 parágrafos diretos e amigáveis, fluindo como a conversa de um Coach especializado na beira da quadra."""
        
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
