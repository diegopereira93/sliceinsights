from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from cachetools import TTLCache
from app.db.database import get_session

router = APIRouter()
_quality_cache = TTLCache(maxsize=1, ttl=300)


def _classify_global_status(failing: int) -> str:
    if failing == 0:
        return "healthy"
    elif failing <= 2:
        return "degraded"
    return "critical"


@router.get("/dashboard")
async def quality_dashboard(session: AsyncSession = Depends(get_session)):
    if "data" in _quality_cache:
        return _quality_cache["data"]

    result = await session.execute(text("""
        SELECT DISTINCT ON (scraper_name)
            scraper_name, freshness_hours, completeness_pct,
            coverage_pct, product_count, error_rate, status, checked_at
        FROM quality_metrics
        WHERE scraper_name != '__consolidated__'
        ORDER BY scraper_name, checked_at DESC
    """))
    rows = result.fetchall()

    scrapers = []
    failing = 0
    for row in rows:
        row_dict = row._mapping
        scraper_data = {
            "name": row_dict["scraper_name"],
            "freshness_hours": round(float(row_dict["freshness_hours"]), 1),
            "completeness_pct": round(float(row_dict["completeness_pct"]), 1),
            "coverage_pct": round(float(row_dict["coverage_pct"]), 1),
            "product_count": row_dict["product_count"],
            "error_rate": round(float(row_dict["error_rate"]), 3),
            "status": row_dict["status"],
            "last_checked": row_dict["checked_at"].isoformat() + "Z"
                if row_dict["checked_at"] else None,
        }
        if row_dict["status"] == "fail":
            failing += 1
        scrapers.append(scraper_data)

    response = {
        "status": _classify_global_status(failing),
        "scrapers": scrapers,
        "summary": {
            "total_scrapers": len(scrapers),
            "passing": len(scrapers) - failing,
            "failing": failing,
        },
    }
    _quality_cache["data"] = response
    return response
