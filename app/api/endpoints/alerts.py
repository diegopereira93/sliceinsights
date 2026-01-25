from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from pydantic import BaseModel, EmailStr
from decimal import Decimal
from uuid import UUID
import structlog

from app.db.database import get_session
from app.models.price_alert import PriceAlert
from app.api.dependencies import get_rate_limiter

logger = structlog.get_logger()

router = APIRouter(prefix="/alerts", tags=["Alerts"])

class AlertCreate(BaseModel):
    paddle_id: UUID
    user_email: EmailStr
    target_price: Decimal

class AlertResponse(BaseModel):
    id: int
    message: str

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_in: AlertCreate,
    session: Session = Depends(get_session),
    limiter = Depends(get_rate_limiter) # Apply rate limiting
):
    """
    Subscribe to a price alert for a specific paddle.
    """
    # Check if active alert already exists for this user/paddle
    # We allow multiple if target price is significantly different, but for MVP let's dedup simple duplicates
    # Implementation: Just create a new record for now to allow history tracking
    
    alert = PriceAlert(
        paddle_id=alert_in.paddle_id,
        user_email=alert_in.user_email,
        target_price=alert_in.target_price,
        is_active=True
    )
    
    try:
        session.add(alert)
        session.commit()
        session.refresh(alert)
        
        logger.info(
            "price_alert_created", 
            alert_id=alert.id, 
            email=alert.user_email, 
            paddle=str(alert.paddle_id)
        )
        
        return AlertResponse(
            id=alert.id,
            message="Alerta criado com sucesso. Você será notificado se o preço atingir sua meta."
        )
    except Exception as e:
        logger.error("alert_creation_failed", error=str(e))
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar alerta."
        )
