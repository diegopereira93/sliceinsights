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
        self.model_name = "llama-3.3-70b-versatile"
        
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
        """
        if not self.client:
            return "O treinador identificou que essas raquetes são as melhores do mercado para o seu perfil técnico."
        
        system_prompt = """Você é um Treinador de Pickleball Profissional e Influente.

DADOS ESTRUTURADOS fornecidos:
- Perfil do Aluno: nível, estilo de jogo, orçamento, restrições físicas
- Raquetes Filtradas: specs técnicos, ratings, custo-benefício

DIRETRIZES DE RECOMENDAÇÃO:
1. Fale DIRETAMENTE com o usuário em segunda pessoa (use "você", "seu", "sua").
2. NUNCA se refira ao usuário como "o aluno", "o jogador" ou "o usuário".
3. Comece o dossiê mencionando a raquete número 1 pelo nome (Ex: "Sua melhor escolha é a [Nome]").
4. Avalie o campo "specs_confidence" para ajustar seu tom.
5. NUNCA mencione variáveis de sistema como `specs_confidence` ou `value_score`.
6. Seja natural, cite marcas e modelos reais.
7. Vocabulário de Treinador Profissional.

CONTEÚDO:
- 2 a 3 parágrafos diretos e amigáveis."""
        
        user_prompt = f"Perfil do Aluno: {user_profile}\n\nRaquetes: {top_paddles}"
        
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
            logger.error("Error in dossier generation", error=str(e))
            return "Sugestões filtradas com rigor pelo nosso algoritmo."

    async def generate_ai_recommendations(self, user_profile: Dict[str, Any], candidate_paddles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ranks candidate paddles and generates a personal dossier in a single LLM pass.
        """
        if not self.client or not candidate_paddles:
            return {
                "ranked_ids": [p["id"] for p in candidate_paddles[:3]],
                "dossier": "O treinador selecionou estas opções com base no estoque disponível."
            }

        system_prompt = """Você é o Algoritmo de Inteligência de Elite do SliceInsights.
Sua missão é atuar como um Treinador de Pickleball Especialista.

REGRAS DE RANKING (CRÍTICO):
1. **Nível de Habilidade**: 
   - Se o usuário for ADVANCED (Avançado), NUNCA recomende raquetes com "Start", "Beginner" ou modelos de entrada, a menos que o orçamento seja extremamente baixo (< R$ 500). Priorize marcas de performance (Paddletek, Joola, Proxr, Engage).
   - Se o usuário for BEGINNER (Iniciante), priorize raquetes amigáveis (sweet spot grande, 16mm).
2. **Estilo de Jogo**:
   - CONTROL: Priorize 16mm ou termos como "Control/Touch/Soft".
   - POWER: Priorize 13-14mm ou termos como "Power/Attack/Speed/TKO/Bantam".
   - BALANCED: Procure raquetes híbridas ou marcas premium versáteis.
3. **Budget vs Qualidade**: Se o orçamento permitir, nunca escolha o modelo mais barato só por segurança. Procure a melhor tecnologia que o dinheiro pode comprar.
5. **Dossiê Direto e Pessoal (CRÍTICO)**: 
   - Fale DIRETAMENTE com o usuário (use "você"). Proibido usar "o aluno".
   - Comece o texto citando o modelo que ficou em 1º lugar como o seu "Match Perfeito".
   - Reconheça explicitamente a existência das outras 2 sugestões do Top 3 logo na sequência.
   - Explique por que estas 3 foram as únicas selecionadas (estilo, orçamento e segurança).
   - Evite introduções genéricas.

SAÍDA OBRIGATÓRIA (JSON):
Responda APENAS o JSON:
{
  "ranked_ids": ["uuid1", "uuid2", "uuid3"],
  "dossier": "O Match Perfeito para você é a [Raquete 1]. Também selecionei a [Raquete 2] e a [Raquete 3] como alternativas sólidas porque seu estilo..."
}"""

        user_prompt = f"Perfil: {user_profile}\nCandidatos: {candidate_paddles}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error("Error in AI ranking", error=str(e))
            return {
                "ranked_ids": [p["id"] for p in candidate_paddles[:3]],
                "dossier": "A IA encontrou um gargalo, mas as sugestões acima foram filtradas pelo algoritmo reserva."
            }

    async def chat_with_context(self, chat_history: List[Dict[str, str]], context: str) -> str:
        """Consultor Técnico de Raquetes Chat."""
        if not self.client:
            return "Chat indisponível."
            
        system_prompt = f"""Você é o Consultor Técnico Especialista do SliceInsights.
Sua missão é ajudar o usuário a entender profundamente as raquetes recomendadas: {context}

DIRETRIZES:
1. Responda com foco técnico nos modelos citados no contexto.
2. Se o usuário pedir por outras opções, você pode mencionar que estas 3 foram as pré-selecionadas pelo algoritmo de elite, mas mantenha a conversa útil e informativa.
3. Não invente especificações técnicas. Use os dados de core, superfície e peso fornecidos.
"""
        messages = [{"role": "system", "content": system_prompt}] + chat_history
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error in Coach Chatbot", error=str(e))
            return "Tente novamente em instantes."

# Singleton
llm_service = LLMService()
