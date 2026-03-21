from typing import Optional, Dict, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from google.cloud.firestore import AsyncClient, Client, CollectionReference, Query
import asyncio

from app.config import get_settings
from app.models.slo_alert import SLOBreach

settings = get_settings()

COLLECTION_SLO_LOGS = "slo_logs"
COLLECTION_SLO_ALERTS = "slo_alerts"


@dataclass
class SLOLogDoc:
    """Firestore document representation of SLO log."""
    id: str
    scraper_name: str
    metric_type: str
    value_hours: float
    threshold_hours: float
    status: str
    checked_at: datetime
    details: Dict


async def get_slo_logs_collection(client: AsyncClient) -> CollectionReference:
    """Get slo_logs collection reference."""
    return client.collection(COLLECTION_SLO_LOGS)


async def get_slo_alerts_collection(client: AsyncClient) -> CollectionReference:
    """Get slo_alerts collection reference."""
    return client.collection(COLLECTION_SLO_ALERTS)


async def get_recent_slo_failures(
    client: AsyncClient,
    lookback_hours: int = 7,
    scraper_name: Optional[str] = None,
) -> List[SLOLogDoc]:
    """Get recent SLO failures from Firestore."""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    col = await get_slo_logs_collection(client)
    
    query = col.where("status", "==", "fail").where("checked_at", ">=", cutoff)
    
    if scraper_name:
        query = query.where("scraper_name", "==", scraper_name)
    
    docs = await query.order_by("checked_at", direction=Query.DESCENDING).get()
    
    return [
        SLOLogDoc(
            id=doc.id,
            scraper_name=doc.get("scraper_name"),
            metric_type=doc.get("metric_type"),
            value_hours=doc.get("value_hours"),
            threshold_hours=doc.get("threshold_hours"),
            status=doc.get("status"),
            checked_at=doc.get("checked_at"),
            details=doc.get("details", {}),
        )
        for doc in docs
    ]


async def get_recent_slo_passes(
    client: AsyncClient,
    lookback_hours: int = 7,
    scraper_name: Optional[str] = None,
) -> List[SLOLogDoc]:
    """Get recent SLO passes from Firestore."""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    col = await get_slo_logs_collection(client)
    
    query = col.where("status", "in", ["pass", "skip"]).where("checked_at", ">=", cutoff)
    
    if scraper_name:
        query = query.where("scraper_name", "==", scraper_name)
    
    docs = await query.order_by("checked_at", direction=Query.DESCENDING).get()
    
    return [
        SLOLogDoc(
            id=doc.id,
            scraper_name=doc.get("scraper_name"),
            metric_type=doc.get("metric_type"),
            value_hours=doc.get("value_hours"),
            threshold_hours=doc.get("threshold_hours"),
            status=doc.get("status"),
            checked_at=doc.get("checked_at"),
            details=doc.get("details", {}),
        )
        for doc in docs
    ]


async def get_alert_state(
    client: AsyncClient,
    scraper_name: str,
    metric_type: str,
) -> Optional[Dict]:
    """Get alert throttle state for a scraper/metric."""
    col = await get_slo_alerts_collection(client)
    docs = await col.where("scraper_name", "==", scraper_name).where("metric_type", "==", metric_type).get()
    
    if docs:
        doc = docs[0]
        return {"id": doc.id, **doc.to_dict()}
    return None


async def upsert_alert_state(
    client: AsyncClient,
    scraper_name: str,
    metric_type: str,
) -> None:
    """Upsert alert state (create or update)."""
    col = await get_slo_alerts_collection(client)
    docs = await col.where("scraper_name", "==", scraper_name).where("metric_type", "==", metric_type).get()
    
    now = datetime.now(timezone.utc)
    
    if docs:
        doc_ref = col.document(docs[0].id)
        await doc_ref.update({
            "last_alert_time": now,
            "updated_at": now,
        })
    else:
        await col.add({
            "scraper_name": scraper_name,
            "metric_type": metric_type,
            "last_alert_time": now,
            "status": "active",
            "alert_count": 1,
            "created_at": now,
            "updated_at": now,
        })


async def clear_alert_throttle(
    client: AsyncClient,
    scraper_name: str,
    metric_type: str,
) -> None:
    """Clear alert throttle when SLO recovers."""
    col = await get_slo_alerts_collection(client)
    docs = await col.where("scraper_name", "==", scraper_name).where("metric_type", "==", metric_type).get()
    
    if docs:
        doc_ref = col.document(docs[0].id)
        await doc_ref.update({
            "status": "resolved",
            "updated_at": datetime.now(timezone.utc),
        })


async def should_send_alert_firestore(
    client: AsyncClient,
    scraper_name: str,
    metric_type: str,
    throttle_hours: int = 6,
) -> bool:
    """Check if alert should be sent (throttled)."""
    from datetime import timedelta
    
    state = await get_alert_state(client, scraper_name, metric_type)
    
    if not state:
        return True
    
    last_alert = state.get("last_alert_time")
    if not last_alert:
        return True
    
    if isinstance(last_alert, str):
        last_alert = datetime.fromisoformat(last_alert.replace("Z", "+00:00"))
    
    if datetime.now(timezone.utc) - last_alert > timedelta(hours=throttle_hours):
        return True
    
    return False
