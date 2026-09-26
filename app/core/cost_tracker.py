"""
Cost tracking for Gemini API calls.
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import CostLog as CostLogModel


def log_gemini_call(
    db: Session,
    call_type: str,
    model: str,
    cost_usd: float,
    image_id: int = None,
    post_id: int = None,
    status: str = "success",
) -> str:
    """
    Log a Gemini API call cost to the database.

    Args:
        db: Database session
        call_type: "vision_analysis" or "embedding"
        model: Model name (e.g., "gemini-2.0-flash")
        cost_usd: Cost in USD
        image_id: Associated image ID if applicable
        post_id: Associated post ID if applicable
        status: "success" or "error"

    Returns:
        call_id: Unique identifier for this call
    """
    call_id = str(uuid.uuid4())

    cost_log = CostLogModel(
        call_id=call_id,
        call_type=call_type,
        model=model,
        cost_usd=cost_usd,
        image_id=image_id,
        post_id=post_id,
        status=status,
        timestamp=datetime.utcnow(),
    )

    db.add(cost_log)
    db.commit()

    return call_id


def get_total_cost(db: Session) -> float:
    """Get total cost across all logged calls."""
    result = db.query(CostLogModel).all()
    return sum(log.cost_usd for log in result)


def get_costs_by_type(db: Session) -> dict:
    """Get cost breakdown by call type."""
    logs = db.query(CostLogModel).all()
    by_type = {}
    for log in logs:
        if log.call_type not in by_type:
            by_type[log.call_type] = 0.0
        by_type[log.call_type] += log.cost_usd
    return by_type
