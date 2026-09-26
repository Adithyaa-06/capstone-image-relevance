"""
Tests for guard logic.
"""

import pytest
from app.core.guard import evaluate_match, GuardDecision


def test_guard_accepts_high_confidence_high_similarity():
    """Test that high confidence and similarity pass guard."""
    decision = evaluate_match(
        image_confidence=0.95,
        similarity_score=0.85,
    )

    assert decision.approved is True
    assert "passed" in decision.reason.lower()


def test_guard_rejects_low_image_confidence():
    """Test that low image confidence is rejected."""
    decision = evaluate_match(
        image_confidence=0.80,
        similarity_score=0.90,
    )

    assert decision.approved is False
    assert "confidence" in decision.reason.lower()


def test_guard_rejects_low_similarity():
    """Test that low similarity score is rejected."""
    decision = evaluate_match(
        image_confidence=0.90,
        similarity_score=0.70,
    )

    assert decision.approved is False
    assert "similarity" in decision.reason.lower()


def test_guard_at_exact_thresholds():
    """Test guard behavior at exact threshold values."""
    # Exactly at threshold should pass
    decision = evaluate_match(
        image_confidence=0.85,
        similarity_score=0.75,
    )

    assert decision.approved is True


def test_guard_just_below_confidence_threshold():
    """Test rejection just below confidence threshold."""
    decision = evaluate_match(
        image_confidence=0.8499,
        similarity_score=0.80,
    )

    assert decision.approved is False


def test_guard_just_below_similarity_threshold():
    """Test rejection just below similarity threshold."""
    decision = evaluate_match(
        image_confidence=0.90,
        similarity_score=0.7499,
    )

    assert decision.approved is False


def test_guard_custom_thresholds():
    """Test guard with custom thresholds."""
    decision = evaluate_match(
        image_confidence=0.75,
        similarity_score=0.65,
        min_confidence=0.70,
        min_similarity=0.60,
    )

    assert decision.approved is True


def test_guard_decision_confidence_score():
    """Test that confidence score is set correctly."""
    decision = evaluate_match(
        image_confidence=0.90,
        similarity_score=0.85,
    )

    assert decision.confidence_score == 0.85  # min of two values


def test_guard_decision_confidence_score_on_rejection():
    """Test confidence score on rejection."""
    decision = evaluate_match(
        image_confidence=0.80,
        similarity_score=0.90,
    )

    assert decision.confidence_score == 0.80
