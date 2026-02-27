import asyncio
from app.db.database import get_session
from app.services.recommendation_engine import RecommendationEngine
from app.schemas.user_profile import UserProfile
from app.models.enums import SkillLevel, PlayStyle

async def main():
    async for session in get_session():
        engine = RecommendationEngine(session)
        profile = UserProfile(
            skill_level=SkillLevel.INTERMEDIATE,
            play_style=PlayStyle.CONTROL,
            budget_max_brl=1600.0,
            has_tennis_elbow=False
        )
        result = await engine.get_recommendations(profile, limit=5)
        for r in result.recommendations:
            print(f"Rank {r.rank}: {r.brand_name} {r.model_name} | Value: {r.value_score} | Ratings: {r.ratings}")
        break

if __name__ == "__main__":
    asyncio.run(main())
