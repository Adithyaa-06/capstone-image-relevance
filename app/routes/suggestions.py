"""
Image suggestion routes for post matching.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import json
from app.models.database import Image, Post, Suggestion
from app.models.schemas import SuggestionResponse, NoMatchResponse, ApprovalRequest, RejectionRequest
from app.core.guard import evaluate_match
from app.core.database import get_db
from datetime import datetime

router = APIRouter(prefix="/posts", tags=["suggestions"])


def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec_a or not vec_b:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


@router.get("/{post_id}/images", response_model=List[SuggestionResponse] | NoMatchResponse)
async def get_image_suggestions(
    post_id: int,
    db: Session = Depends(get_db),
):
    """
    Get top image suggestions for a post.
    Uses embedding similarity + guard logic.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.embedding:
        raise HTTPException(status_code=400, detail="Post embedding not generated yet")

    images = db.query(Image).all()
    scored_images = []

    for image in images:
        if not image.embedding:
            continue

        similarity = cosine_similarity(post.embedding, image.embedding)
        guard = evaluate_match(
            image_confidence=image.confidence,
            similarity_score=similarity,
        )

        scored_images.append({
            "image": image,
            "similarity": similarity,
            "guard": guard,
        })

    scored_images.sort(key=lambda x: x["similarity"], reverse=True)

    top_suggestions = scored_images[:5]
    approved_suggestions = [s for s in top_suggestions if s["guard"].approved]

    if not approved_suggestions:
        reasons = []
        if top_suggestions:
            top = top_suggestions[0]
            if not top["guard"].approved:
                reasons.append(top["guard"].reason)

        return NoMatchResponse(
            post_id=post_id,
            reasons=reasons,
        )

    results = []
    for match in approved_suggestions:
        image = match["image"]
        guard = match["guard"]
        similarity = match["similarity"]

        existing = db.query(Suggestion).filter(
            Suggestion.post_id == post_id,
            Suggestion.image_id == image.id,
        ).first()

        if not existing:
            suggestion = Suggestion(
                post_id=post_id,
                image_id=image.id,
                similarity_score=similarity,
                guard_decision="approved",
                guard_reason=guard.reason,
            )
            db.add(suggestion)
            db.commit()
            db.refresh(suggestion)
        else:
            suggestion = existing

        results.append(SuggestionResponse(
            suggestion_id=suggestion.id,
            post_id=post_id,
            image_id=image.id,
            filename=image.filename,
            subject=image.subject,
            similarity_score=similarity,
            status=suggestion.status,
            guard_decision="approved",
            guard_reason=guard.reason,
            approved_at=suggestion.approved_at.isoformat() if suggestion.approved_at else None,
        ))

    return results


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve an image suggestion."""
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = "approved"
    suggestion.approved_at = datetime.utcnow()
    db.commit()

    return {
        "suggestion_id": suggestion.id,
        "status": "approved",
        "approved_at": suggestion.approved_at.isoformat(),
    }


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: int,
    request: RejectionRequest,
    db: Session = Depends(get_db),
):
    """Reject an image suggestion."""
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    suggestion.status = "rejected"
    suggestion.rejected_at = datetime.utcnow()
    db.commit()

    return {
        "suggestion_id": suggestion.id,
        "status": "rejected",
        "reason": request.reason,
        "rejected_at": suggestion.rejected_at.isoformat(),
    }
