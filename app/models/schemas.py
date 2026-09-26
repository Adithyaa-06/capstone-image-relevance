from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ImageCategory(str, Enum):
    ANIMAL = "animal"
    PLANT = "plant"
    LANDSCAPE = "landscape"
    ARCHITECTURE = "architecture"
    OTHER = "other"

class ImageTag(BaseModel):
    """Schema-validated image metadata from vision model"""
    subject: str = Field(..., min_length=1, max_length=100)
    category: ImageCategory
    attributes: List[str] = Field(..., min_items=1, max_items=10)
    caption: str = Field(..., min_length=10, max_length=500)
    confidence: float = Field(..., ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "red fox",
                "category": "animal",
                "attributes": ["orange fur", "wild", "forest"],
                "caption": "A red fox standing alert in a snowy forest",
                "confidence": 0.94
            }
        }

class ImageRecord(BaseModel):
    id: int
    filename: str
    subject: str
    category: str
    attributes: List[str]
    caption: str
    confidence: float
    flagged: bool = False
    flagged_reason: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: str

class PostRecord(BaseModel):
    id: int
    title: str
    content: str
    embedding: Optional[List[float]] = None
    created_at: str

class SuggestionResponse(BaseModel):
    suggestion_id: int
    post_id: int
    image_id: int
    filename: str
    subject: str
    similarity_score: float
    status: str = "pending"
    guard_decision: str
    guard_reason: str
    approved_at: Optional[str] = None

class NoMatchResponse(BaseModel):
    post_id: int
    message: str = "No confident match found"
    reasons: List[str]

class ApprovalRequest(BaseModel):
    feedback: Optional[str] = None

class RejectionRequest(BaseModel):
    reason: str = Field(..., min_length=5)
    feedback: Optional[str] = None

class CostLog(BaseModel):
    call_id: str
    call_type: str
    model: str
    image_id: Optional[int] = None
    post_id: Optional[int] = None
    cost_usd: float
    timestamp: str
    status: str = "success"

class PrecisionResult(BaseModel):
    total_posts: int
    correct_top1: int
    precision: float
    details: List[dict] = []