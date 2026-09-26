"""
Cost tracking and logging routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import CostLog
from app.models.schemas import CostLog as CostLogSchema
from app.core.database import get_db
from typing import List

router = APIRouter(prefix="/cost-log", tags=["costs"])


@router.get("", response_model=List[CostLogSchema])
async def get_cost_logs(
    skip: int = 0,
    limit: int = 100,
    call_type: str = None,
    db: Session = Depends(get_db),
):
    """Get cost logs with optional filtering."""
    query = db.query(CostLog)

    if call_type:
        query = query.filter(CostLog.call_type == call_type)

    logs = query.offset(skip).limit(limit).all()

    return [
        CostLogSchema(
            call_id=log.call_id,
            call_type=log.call_type,
            model=log.model,
            cost_usd=log.cost_usd,
            timestamp=log.timestamp.isoformat(),
            status=log.status,
        )
        for log in logs
    ]


@router.get("/summary")
async def get_cost_summary(db: Session = Depends(get_db)):
    """Get cost summary grouped by call type."""
    logs = db.query(CostLog).all()

    by_type = {}
    total = 0.0

    for log in logs:
        total += log.cost_usd
        if log.call_type not in by_type:
            by_type[log.call_type] = {
                "count": 0,
                "total_cost": 0.0,
            }
        by_type[log.call_type]["count"] += 1
        by_type[log.call_type]["total_cost"] += log.cost_usd

    return {
        "total_cost": total,
        "by_type": by_type,
        "total_calls": len(logs),
    }
