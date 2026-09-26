"""
Tests for Pydantic schema validation.
"""

import pytest
from pydantic import ValidationError
from app.models.schemas import (
    ImageTag,
    ImageRecord,
    PostRecord,
    SuggestionResponse,
    ApprovalRequest,
    RejectionRequest,
    CostLog,
    PrecisionResult,
)


def test_image_tag_valid():
    """Test valid ImageTag creation."""
    tag = ImageTag(
        subject="red fox",
        category="animal",
        attributes=["orange fur", "wild", "forest"],
        caption="A red fox standing in a snowy forest clearing",
        confidence=0.94,
    )

    assert tag.subject == "red fox"
    assert tag.category == "animal"
    assert len(tag.attributes) == 3
    assert tag.confidence == 0.94


def test_image_tag_invalid_confidence():
    """Test ImageTag rejects invalid confidence."""
    with pytest.raises(ValidationError):
        ImageTag(
            subject="red fox",
            category="animal",
            attributes=["fur", "wild"],
            caption="A red fox in the forest",
            confidence=1.5,  # Invalid: > 1.0
        )


def test_image_tag_invalid_category():
    """Test ImageTag rejects invalid category."""
    with pytest.raises(ValidationError):
        ImageTag(
            subject="red fox",
            category="invalid_category",
            attributes=["fur", "wild"],
            caption="A red fox in the forest",
            confidence=0.95,
        )


def test_image_tag_caption_too_short():
    """Test ImageTag rejects caption below minimum length."""
    with pytest.raises(ValidationError):
        ImageTag(
            subject="fox",
            category="animal",
            attributes=["fur"],
            caption="Short",  # < 10 chars
            confidence=0.95,
        )


def test_image_tag_too_few_attributes():
    """Test ImageTag rejects with too few attributes."""
    with pytest.raises(ValidationError):
        ImageTag(
            subject="fox",
            category="animal",
            attributes=[],  # Empty list
            caption="A red fox in the forest",
            confidence=0.95,
        )


def test_image_record_valid():
    """Test valid ImageRecord creation."""
    record = ImageRecord(
        id=1,
        filename="fox.jpg",
        subject="red fox",
        category="animal",
        attributes=["fur", "wild"],
        caption="A red fox in the forest",
        confidence=0.94,
        flagged=False,
        created_at="2024-01-01T00:00:00",
    )

    assert record.id == 1
    assert record.filename == "fox.jpg"
    assert record.flagged is False


def test_post_record_valid():
    """Test valid PostRecord creation."""
    record = PostRecord(
        id=1,
        title="Wildlife",
        content="A discussion about wildlife",
        created_at="2024-01-01T00:00:00",
    )

    assert record.id == 1
    assert record.title == "Wildlife"


def test_suggestion_response_valid():
    """Test valid SuggestionResponse creation."""
    response = SuggestionResponse(
        suggestion_id=1,
        post_id=1,
        image_id=1,
        filename="fox.jpg",
        subject="red fox",
        similarity_score=0.85,
        status="pending",
        guard_decision="approved",
        guard_reason="Match passed all checks",
    )

    assert response.suggestion_id == 1
    assert response.similarity_score == 0.85


def test_approval_request_valid():
    """Test valid ApprovalRequest creation."""
    request = ApprovalRequest(
        feedback="Good match",
    )

    assert request.feedback == "Good match"


def test_rejection_request_valid():
    """Test valid RejectionRequest creation."""
    request = RejectionRequest(
        reason="Image does not match content",
        feedback="Not relevant",
    )

    assert request.reason == "Image does not match content"


def test_rejection_request_invalid_reason():
    """Test RejectionRequest rejects short reason."""
    with pytest.raises(ValidationError):
        RejectionRequest(
            reason="Bad",  # < 5 chars
        )


def test_cost_log_valid():
    """Test valid CostLog creation."""
    log = CostLog(
        call_id="abc-123",
        call_type="vision_analysis",
        model="gemini-2.0-flash",
        cost_usd=0.001,
        timestamp="2024-01-01T00:00:00",
    )

    assert log.call_id == "abc-123"
    assert log.cost_usd == 0.001


def test_precision_result_valid():
    """Test valid PrecisionResult creation."""
    result = PrecisionResult(
        total_posts=100,
        correct_top1=85,
        precision=0.85,
    )

    assert result.total_posts == 100
    assert result.precision == 0.85
