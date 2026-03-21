from typing import List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timedelta

from app.db.database import get_session
from app.models.price_snapshot import PriceSnapshot

router = APIRouter()

@router.get("/{paddle_id}/history")
async def get_paddle_history(
    paddle_id: UUID,
    days: int = 30,
    session: AsyncSession = Depends(get_session)
):
    """
    Returns historical price data for a specific paddle.
    Returns the last 'days' of snapshots, grouped by store.
    """
    # Calculate cutoff date
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    query = (
        select(PriceSnapshot)
        .where(PriceSnapshot.paddle_id == paddle_id)
        .where(PriceSnapshot.snapshot_date >= cutoff_date)
        .order_by(PriceSnapshot.snapshot_date, PriceSnapshot.captured_at)
    )
    
    result = await session.exec(query)
    snapshots = result.all()
    
    if not snapshots:
        return {"paddle_id": str(paddle_id), "history": []}
        
    # Group by store for easier frontend chart consumption
    history_by_store: Dict[str, List[dict]] = {}
    
    for s in snapshots:
        if s.store_name not in history_by_store:
            history_by_store[s.store_name] = []
            
        history_by_store[s.store_name].append({
            "date": s.snapshot_date,
            "price_brl": float(s.price_brl),
            "is_available": s.is_available
        })
        
    return {
        "paddle_id": str(paddle_id),
        "history": history_by_store
    }
