"""
SliceInsights Pickleball Chat - Recomendações por Linguagem Natural

Usa Groq (LPU) para responder perguntas sobre raquetes de Pickleball em português.
Inspirado no Lakehouse Chat do projeto lakehouse.
"""

import os
import streamlit as st
import psycopg2
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv("../../.env")

# Configuração da página
st.set_page_config(
    page_title="Pickleball Chat - SliceInsights",
    page_icon="🏓",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .stTextArea textarea { font-family: 'Fira Code', monospace; }
    .main { background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%); }
    h1 { color: #CEFF00 !important; }
</style>
""", unsafe_allow_html=True)


# Schema das tabelas para contexto do LLM
SCHEMA_CONTEXT = """
Você é um especialista em raquetes de Pickleball focado no mercado brasileiro.
Responda perguntas de forma amigável, clara e objetiva, sempre em português.

TABELAS DISPONÍVEIS (PostgreSQL):

1. paddle_master (460+ raquetes)
   - id (UUID, PK)
   - model_name (TEXT): Nome do modelo
   - brand_id (INTEGER): Referência para brands
   - power_rating, control_rating (INTEGER 0-10): Notas de potência e controle
   - core_material (TEXT): Polímero, Nomex, Alumínio
   - face_material (TEXT): Carbono, Fibra de Vidro, Híbrido
   - shape (TEXT): Standard, Elongated, Widebody
   - core_thickness_mm (FLOAT): Espessura do núcleo
   - skill_level (TEXT): beginner, intermediate, advanced
   - ideal_for_tennis_elbow (BOOLEAN): Se é indicada para lesões
   - available_in_brazil (BOOLEAN): Disponível no Brasil
   - is_featured (BOOLEAN): Raquete destaque

2. brands (50 marcas)
   - id (INTEGER, PK)
   - name (TEXT): Nome da marca (Selkirk, CRBN, Joola, etc)
   - website (TEXT)

3. market_offers (preços atuais)
   - paddle_id (UUID): Referência para paddle_master
   - store_name (TEXT): Nome da loja (Brazil Pickleball Store, etc)
   - price_brl (DECIMAL): Preço em Reais
   - url (TEXT): Link para compra
   - is_active (BOOLEAN)

REGRAS:
- Foque em raquetes disponíveis no Brasil (available_in_brazil = true)
- Sempre inclua o preço quando disponível
- Use JOINs para combinar paddle_master, brands e market_offers
- Se a pergunta for sobre recomendação, ordene por relevância
- Limite resultados a 5-10 raquetes por padrão
- Retorne APENAS o SQL, sem explicações

EXEMPLOS DE PERGUNTAS:
- "Qual a melhor raquete para iniciante?"
- "Raquetes de carbono abaixo de R$500"
- "Selkirk vs CRBN para potência"
- "Raquete boa para quem tem lesão no cotovelo"
"""


def get_db_connection():
    """Conecta ao PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5434"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "picklematch"),
    )


def generate_sql(question: str, api_key: str) -> str:
    """Usa Groq para gerar SQL a partir da pergunta."""
    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SCHEMA_CONTEXT},
            {"role": "user", "content": f"Gere um SQL para: {question}"}
        ],
        temperature=0.1,
        max_tokens=1024
    )
    
    sql = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks se presentes
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    sql = sql.strip()
    
    return sql


def generate_response(question: str, sql: str, df: pd.DataFrame, api_key: str) -> str:
    """Gera uma resposta em linguagem natural baseada nos resultados."""
    client = Groq(api_key=api_key)
    
    # Converter DataFrame para texto resumido
    if len(df) > 0:
        results_text = df.head(10).to_string()
    else:
        results_text = "Nenhum resultado encontrado"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system", 
                "content": """Você é um especialista em Pickleball que ajuda jogadores a escolher raquetes.
                Responda de forma amigável e conversacional em português brasileiro.
                Use emojis para tornar a resposta mais envolvente.
                Se houver raquetes recomendadas, destaque as melhores opções com seus pontos fortes.
                Sempre mencione o preço quando disponível."""
            },
            {
                "role": "user", 
                "content": f"""Pergunta original: {question}

Resultados da consulta:
{results_text}

Por favor, responda à pergunta de forma amigável baseada nesses resultados."""
            }
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    return response.choices[0].message.content


def execute_sql(sql: str) -> pd.DataFrame:
    """Executa SQL e retorna DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql(sql, conn)
        return df
    finally:
        conn.close()


# UI Principal
st.title("🏓 Pickleball Chat")
st.markdown("**Pergunte qualquer coisa sobre raquetes de Pickleball!**")

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # API Key
    api_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Obtenha grátis em https://console.groq.com/"
    )
    
    st.divider()
    
    st.markdown("### 💡 Exemplos de perguntas")
    st.markdown("""
    - Qual a melhor raquete para iniciante?
    - Raquetes de carbono abaixo de R$1000
    - Comparar Selkirk e CRBN
    - Boa opção para quem tem cotovelo de tenista
    - Top 5 custo-benefício
    """)
    
    st.divider()
    
    show_sql = st.checkbox("Mostrar SQL gerado", value=False)

# Input da pergunta
col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_input(
        "Sua pergunta:",
        placeholder="Ex: Qual a melhor raquete para quem vem do tênis?",
        label_visibility="collapsed"
    )
with col2:
    generate_btn = st.button("🔍 Perguntar", type="primary", use_container_width=True)

# Processamento
if generate_btn and question:
    if not api_key:
        st.error("⚠️ Configure a API Key do Groq na barra lateral")
    else:
        with st.spinner("🤖 Analisando sua pergunta..."):
            try:
                # Gera SQL
                sql = generate_sql(question, api_key)
                
                # Mostra SQL gerado (opcional)
                if show_sql:
                    with st.expander("📝 SQL Gerado", expanded=False):
                        st.code(sql, language="sql")
                
                # Executa SQL
                with st.spinner("⚡ Buscando raquetes..."):
                    df = execute_sql(sql)
                
                # Gera resposta em linguagem natural
                with st.spinner("💬 Preparando resposta..."):
                    response = generate_response(question, sql, df, api_key)
                
                # Mostra resposta
                st.markdown("### 💬 Resposta")
                st.markdown(response)
                
                # Mostra tabela de resultados
                if len(df) > 0:
                    st.markdown("### 📊 Dados Encontrados")
                    st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                st.info("💡 Tente reformular sua pergunta ou verifique a conexão com o banco.")

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Powered by <b>Groq</b> (Llama 3.3) + <b>SliceInsights</b> 🏓"
    "</div>",
    unsafe_allow_html=True
)
