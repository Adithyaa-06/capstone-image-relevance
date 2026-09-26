"""
Evaluation routes for precision metrics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models.database import EvalSet, Suggestion
from app.models.schemas import PrecisionResult
from app.core.database import get_db

router = APIRouter(prefix="/eval", tags=["evaluation"])


@router.get("/precision", response_model=PrecisionResult)
async def get_precision(db: Session = Depends(get_db)):
    """
    Calculate top-1 precision on evaluation set.

    For each post in eval set, check if top-ranked approved suggestion
    matches the correct image.
    """
    eval_posts = db.query(EvalSet).all()

    if not eval_posts:
        return PrecisionResult(
            total_posts=0,
            correct_top1=0,
            precision=0.0,
            details=[],
        )

    correct_count = 0
    details = []

    for eval_post in eval_posts:
        post_id = eval_post.post_id
        correct_image_id = eval_post.correct_image_id

        suggestions = db.query(Suggestion).filter(
            Suggestion.post_id == post_id,
            Suggestion.status == "approved",
        ).order_by(Suggestion.similarity_score.desc()).all()

        top1_match = False
        top1_image_id = None

        if suggestions:
            top1_image_id = suggestions[0].image_id
            top1_match = (top1_image_id == correct_image_id)

        if top1_match:
            correct_count += 1

        details.append({
            "post_id": post_id,
            "correct_image_id": correct_image_id,
            "top1_image_id": top1_image_id,
            "match": top1_match,
        })

    total = len(eval_posts)
    precision = correct_count / total if total > 0 else 0.0

    return PrecisionResult(
        total_posts=total,
        correct_top1=correct_count,
        precision=precision,
        details=details,
    )
