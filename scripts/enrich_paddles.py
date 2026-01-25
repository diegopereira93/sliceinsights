import asyncio
import os
from typing import Optional
import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.database import engine as db_engine
from app.models.paddle import PaddleMaster
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOP_N = 50 # Focus on top 50 as per roadmap

class EnrichmentAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_and_extract(self, brand: str, model: str) -> dict:
        """
        Simulates searching and extracting data using an LLM.
        In a real scenario, this would call a search API (like Tavily) 
        and then an LLM (like GPT-4) to parse the results.
        """
        if not self.api_key:
            print(f"  [Sim] Searching for {brand} {model}...")
            return {} # Dry run / No API key

        prompt = f"""
        Find technical specifications for the pickleball paddle: {brand} {model}.
        Specifically:
        - Face Material (Carbon Fiber, Graphite, Fiberglass, Hybrid)
        - Core Thickness (mm)
        - Core Material (Polymer, Nomex, Aluminum)
        
        Return ONLY a JSON object with these keys or null if not found.
        """
        
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            print("  Error calling LLM during search and extract.")
            return {}

    async def run(self):
        async with AsyncSession(db_engine) as session:
            # 1. Select paddles with missing data
            # Focusing on face_material as it was highlighted in the roadmap
            query = select(PaddleMaster).where(
                (PaddleMaster.face_material.is_(None)) | (PaddleMaster.core_thickness_mm.is_(None))
            ).limit(TOP_N)
            
            result = await session.exec(query)
            paddles = result.all()
            
            print(f"Found {len(paddles)} paddles needing enrichment.")
            
            for paddle in paddles:
                print(f"Enriching {paddle.model_name}...")
                
                # Fetch Brand Name
                # brand_query = await session.exec(select(PaddleMaster).where(PaddleMaster.id == paddle.id))
                # (Assuming Brand relationship is loaded or accessible)
                # For simplicity, let's use the brand_id to get brand name if needed, 
                # but paddle object might have it if joined.
                brand_name = "Unknown" # Placeholder
                if paddle.brand:
                    brand_name = paddle.brand.name

                raw_specs = await self.search_and_extract(brand_name, paddle.model_name)
                
                if raw_specs:
                    # Logic to update the paddle object
                    # parse and validate...
                    pass

            print("Done.")

async def main():
    agent = EnrichmentAgent(api_key=OPENAI_API_KEY)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
