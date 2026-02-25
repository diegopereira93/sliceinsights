import os
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from openai import OpenAI
import dlt
from typing import Generator

from app.config import get_settings
from app.models.ai_knowledge import AIKnowledgeBase

# Constants
settings = get_settings()

@dlt.source
def influencer_knowledge_source() -> Generator:
    """Creates a DLT source that yields transcript/review objects to be embedded."""
    return influencer_transcripts_resource()

@dlt.resource(write_disposition="append")
def influencer_transcripts_resource():
    """Yields fake transcript blocks simulating the Influencer."""
    transcripts = [
        {
            "source_type": "youtube_video",
            "source_url": "https://youtube.com/watch?v=mock1",
            "title": "A Verdade sobre as Raquetes de Kevlar",
            "content": "Sempre digo aos meus alunos: se você tem epicondilite (tennis elbow), fuja de raquetes muito pesadas ou com pouco sweet spot. O Kevlar tem ajudado muita gente a ter controle sem sentir o impacto no braço.",
        },
        {
            "source_type": "youtube_video",
            "source_url": "https://youtube.com/watch?v=mock2",
            "title": "Raquetes Alongadas (Elongated) valem a pena?",
            "content": "A raquete alongada te dá muito mais alcance (reach) na cozinha e mais alavanca para os drives (power). Mas tome cuidado, se você for iniciante, o sweet spot é menor e você vai bater muita bola na borda (mishit).",
        },
        {
            "source_type": "article",
            "source_url": "https://treinador.com/blog/spin",
            "title": "Como gerar mais Spin",
            "content": "Para gerar spin, eu prezo demais pela textura da raquete (Carbono T700 cru). A física do raw carbon fiber 'morde' a bola. Não compre fibra de vidro brilhosa se o seu jogo depende de topspin do fundo da quadra.",
        }
    ]
    for tr in transcripts:
        yield tr

def get_embedding(text: str, client: OpenAI) -> list[float]:
    """Calls Grok (xAI) or OpenAI to get embeddings for the text."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small" # Ou modelo suportado pelo GROK
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding failed: {e}")
        # Return empty 1536 dim vector for mock purposes
        return [0.1] * 1536

def run_dlt_pipeline():
    """
    Executes the DLT pipeline and inserts the embeddings into the Postgres Vector DB.
    """
    print("🚀 Starting Influencer Knowledge DLT Pipeline...")
    
    # 1. Run DLT pipeline to normalize 
    pipeline = dlt.pipeline(
        pipeline_name='influencer_knowledge_dlt',
        destination='duckdb', # Use local duckdb as staging before Postgres to leverage dlt cheaply
        dataset_name='knowledge_staging'
    )
    
    info = pipeline.run(influencer_knowledge_source())
    print(f"DLT Pipeline ran: {info}")
    
    # 2. Extract from DLT staging and embed to PostgreSQL
    print("Embedding data and saving to PostgreSQL Vector Store...")
    client = OpenAI(
        api_key=settings.grok_api_key or os.getenv("GROK_API_KEY", "dummy"),
        base_url="https://api.x.ai/v1" if settings.grok_api_key else None
    )
    
    engine = create_engine(settings.sync_database_url)
    
    with Session(engine) as session:
        # Get data from DLT duckdb (using simple dicts here to avoid needing duckdb installed in prod)
        for data in influencer_transcripts_resource():
            # Check if exists
            exists = session.query(AIKnowledgeBase).filter(AIKnowledgeBase.title == data["title"]).first()
            if exists:
                print(f"Skipping '{data['title']}', already exists.")
                continue
                
            print(f"Embedding: {data['title']}")
            emb = get_embedding(data["content"], client)
            
            kb_entry = AIKnowledgeBase(
                source_type=data["source_type"],
                source_url=data["source_url"],
                title=data["title"],
                content=data["content"],
                embedding=emb
            )
            session.add(kb_entry)
            
        session.commit()
    print("✅ AI Knowledge Ingestion Complete!")

if __name__ == "__main__":
    run_dlt_pipeline()
