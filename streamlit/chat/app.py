"""
SliceInsights Pickleball Chat - Recomendações por Linguagem Natural

Usa Groq (LPU) para responder perguntas sobre raquetes de Pickleball em português.
Inspirado no Lakehouse Chat do projeto lakehouse.
"""

import os
import sys
import streamlit as st
import psycopg2
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# Add current directory to path to find 'app'
sys.path.append(os.getcwd())

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


@st.cache_data(ttl=3600)  # Cache schema for 1 hour
def get_db_schema():
    """Extrai o schema real das tabelas do PostgreSQL de forma dinâmica."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        tables = ["paddle_master", "brands", "market_offers"]
        schema_text = "Você é um especialista em raquetes de Pickleball focado no mercado brasileiro.\n"
        schema_text += "Responda perguntas de forma amigável, clara e objetiva, sempre em português.\n\n"
        schema_text += "TABELAS DISPONÍVEIS NO BANCO (PostgreSQL):\n\n"
        
        for table in tables:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            columns = cur.fetchall()
            
            schema_text += f"{table.upper()}:\n"
            for col in columns:
                schema_text += f"  - {col[0]} ({col[1]})\n"
            schema_text += "\n"
            
        schema_text += """
REGRAS CRÍTICAS:
- Use APENAS as colunas listadas acima. NÃO invente colunas.
- Foque em raquetes disponíveis no Brasil (paddle_master.available_in_brazil = true)
- Sempre inclua o preço (market_offers.price_brl) quando possível
- Use JOINs: paddle_master pm JOIN brands b ON pm.brand_id = b.id JOIN market_offers mo ON pm.id = mo.paddle_id
- PERFORMANCE: Use as colunas power_rating, control_rating, spin_rating, sweet_spot_rating (0-10) para comparar performance.
- CUSTO-BENEFÍCIO: Calcule mentalmente (média dos ratings / preço). Mostre raquetes com ratings altos e preços baixos primeiro.
- HONESTIDADE: Priorize raquetes onde specs_source = 'lab_dataset'. Se usar uma com 'brazil_scraper' ou nulo, avise que as specs são estimativas.
- Limite resultados a 5 raquetes por padrão
- Retorne APENAS o SQL válido, sem blocos markdown, sem explicações.
"""
        conn.close()
        return schema_text
    except Exception as e:
        return f"Erro ao carregar schema: {e}"


def get_db_connection():
    """Conecta ao PostgreSQL (host-side, fora do Docker)."""
    return psycopg2.connect(
        host=os.getenv("CHAT_DB_HOST", "localhost"),
        port=os.getenv("CHAT_DB_PORT", "5434"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "picklematch"),
    )


def generate_sql(question: str, api_key: str) -> str:
    """Usa Groq para gerar SQL a partir da pergunta."""
    client = Groq(api_key=api_key)
    schema = get_db_schema()
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": schema},
            {"role": "user", "content": f"Gere um SQL SELECT para extrair raquetes que atendam a: {question}"}
        ],
        temperature=0.1,
        max_tokens=1024
    )
    
    sql = response.choices[0].message.content.strip()
    
    # Limpeza robusta do SQL (remove markdown blocks de qualquer tipo)
    if "```" in sql:
        parts = sql.split("```")
        for part in parts:
            if "SELECT" in part.upper():
                sql = part
                break
        if sql.startswith("sql"):
            sql = sql[3:]
    
    return sql.strip()


def generate_response(question: str, df: pd.DataFrame, api_key: str) -> str:
    """Gera uma resposta em linguagem natural baseada nos resultados."""
    client = Groq(api_key=api_key)
    
    if df is not None and not df.empty:
        results_text = df.head(5).to_string()
    else:
        results_text = "Nenhum resultado encontrado no banco de dados para esta busca específica."
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system", 
                "content": """Você é o consultor SliceInsights. 
                Ajude o jogador a escolher a raquete ideal em português brasileiro.
                Use emojis 🏓 e mantenha um tom premium e encorajador.
                IMPORTANTE: Se a raquete tiver specs_source = 'lab_dataset', mencione que ela tem dados verificados de laboratório (🧪).
                Se não tiver, seja honesto e diga que os ratings são estimativas inteligentes (🤖) baseadas em raquetes similares."""
            },
            {
                "role": "user", 
                "content": f"Pergunta: {question}\n\nDados:\n{results_text}\n\nResponda ao usuário:"
            }
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    return response.choices[0].message.content


def execute_sql(sql: str) -> pd.DataFrame:
    """Executa SQL de forma segura (somente SELECT read-only)."""
    # Guard: validate SQL before execution
    normalized = sql.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "EXEC"]

    if not normalized.startswith("SELECT"):
        st.error("⚠️ Apenas consultas SELECT são permitidas.")
        return None
    if ";" in sql.strip().rstrip(";"):
        st.error("⚠️ Múltiplos statements não são permitidos.")
        return None
    for word in forbidden:
        # Check for keyword as a whole word (surrounded by non-alphanumeric)
        import re
        if re.search(rf'\b{word}\b', normalized):
            st.error(f"⚠️ Operação '{word}' não é permitida.")
            return None

    try:
        conn = get_db_connection()
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro na execução da Query: {e}")
        return None


# UI Principal
st.title("🏓 SliceInsights Chat")
st.markdown("O seu consultor inteligente de raquetes de Pickleball.")

# Inicializar histórico
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY", ""), type="password")
    
    st.divider()
    st.markdown("### 💡 Atalhos Rápidos")
    
    q1 = st.button("Melhor custo-benefício (Brasil)", use_container_width=True)
    q2 = st.button("Raquetes de Carbono (Alta Performance)", use_container_width=True)
    q3 = st.button("Opções para Iniciantes", use_container_width=True)
    q4 = st.button("Paddles com foco em Controle", use_container_width=True)
    
    st.divider()
    show_sql = st.checkbox("Debug Mode (Ver SQL)", value=False)
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "df" in message and message["df"] is not None:
            st.dataframe(message["df"])

# Capturar input do usuário (chat ou botões)
user_query = None
if q1:
    user_query = "Quais as raquetes com melhor custo-benefício disponíveis no Brasil?"
elif q2:
    user_query = "Me mostre raquetes de alta performance feitas de fibra de carbono."
elif q3:
    user_query = "Quais são as melhores opções para quem está começando agora?"
elif q4:
    user_query = "Quero raquetes focadas em controle e precisão."

chat_input = st.chat_input("Perqunte sobre marcas, preços ou modelos...")
if chat_input:
    user_query = chat_input

# Processamento
if user_query:
    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    if not api_key:
        st.error("⚠️ Configure a API Key do Groq na barra lateral")
    else:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Analisando banco de dados..."):
                try:
                    # 1. Gera SQL
                    sql = generate_sql(user_query, api_key)
                    if show_sql:
                        st.code(sql, language="sql")
                    
                    # 2. Executa
                    df = execute_sql(sql)
                    
                    # 3. Gera Resposta
                    response = generate_response(user_query, df, api_key)
                    st.markdown(response)
                    
                    if df is not None and not df.empty:
                        # Add Badges for transparency
                        if 'specs_source' in df.columns:
                            df['status'] = df['specs_source'].apply(
                                lambda x: "🧪 Lab Verified" if x == 'lab_dataset' else "🤖 AI Estimated"
                            )
                            # Reorder to put status first
                            cols = ['status'] + [c for c in df.columns if c != 'status']
                            df = df[cols]
                        st.dataframe(df)
                    
                    # Salva no histórico
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "df": df if df is not None and not df.empty else None
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Ocorreu um erro: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
st.caption("Powered by Groq + SliceInsights Intelligence Layer")
