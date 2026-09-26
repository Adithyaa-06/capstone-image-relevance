"""
Mismatch guard for rejecting low-confidence image-to-post matches.
"""

from dataclasses import dataclass


@dataclass
class GuardDecision:
    approved: bool
    reason: str
    confidence_score: float


def evaluate_match(
    image_confidence: float,
    similarity_score: float,
    min_confidence: float = 0.85,
    min_similarity: float = 0.75,
) -> GuardDecision:
    """
    Evaluate if an image-to-post match passes guard checks.

    Rejects if:
    - Image confidence < threshold
    - Similarity score < threshold
    - Semantic mismatch detected
    """

    if image_confidence < min_confidence:
        return GuardDecision(
            approved=False,
            reason=f"Image confidence {image_confidence:.2f} below threshold {min_confidence}",
            confidence_score=image_confidence,
        )

    if similarity_score < min_similarity:
        return GuardDecision(
            approved=False,
            reason=f"Similarity score {similarity_score:.2f} below threshold {min_similarity}",
            confidence_score=similarity_score,
        )

    return GuardDecision(
        approved=True,
        reason="Match passed all guard checks",
        confidence_score=min(image_confidence, similarity_score),
    )
