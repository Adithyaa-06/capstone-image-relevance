"""
Batch process images via Gemini Flash vision model.
Extracts subject, category, attributes, caption, and confidence.
"""

import google.generativeai as genai
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.database import Image
from app.models.schemas import ImageTag
from app.core.cost_tracker import log_gemini_call
import os


def init_gemini():
    """Initialize Gemini API with key from environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    genai.configure(api_key=api_key)


def process_image_file(image_path: str) -> ImageTag:
    """
    Process a single image file with Gemini Flash vision model.

    Args:
        image_path: Path to image file

    Returns:
        ImageTag: Validated image metadata

    Raises:
        ValueError: If vision processing fails
    """
    if not Path(image_path).exists():
        raise ValueError(f"Image file not found: {image_path}")

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        with open(image_path, "rb") as img_file:
            image_data = img_file.read()

        prompt = """Analyze this image and provide ONLY a valid JSON response with exactly these fields:
{
    "subject": "single main subject (1-100 chars)",
    "category": "one of: animal, plant, landscape, architecture, other",
    "attributes": ["list", "of", "3-10", "visual", "attributes"],
    "caption": "descriptive caption (10-500 chars)",
    "confidence": 0.0 to 1.0 (how confident are you in this analysis)
}

Respond with ONLY the JSON, no markdown, no explanation."""

        response = model.generate_content([
            {"mime_type": "image/jpeg" if image_path.lower().endswith('.jpg') else "image/png", "data": image_data},
            prompt
        ])

        try:
            result = json.loads(response.text)
            tag = ImageTag(**result)
            return tag
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from model: {response.text}")

    except Exception as e:
        raise ValueError(f"Vision processing failed: {str(e)}")


def save_image_record(
    db: Session,
    filename: str,
    tag: ImageTag,
    embedding: list = None,
) -> int:
    """
    Save processed image to database.

    Args:
        db: Database session
        filename: Original filename
        tag: Validated image metadata
        embedding: Optional embedding vector

    Returns:
        image_id: ID of saved record
    """
    import json

    image = Image(
        filename=filename,
        subject=tag.subject,
        category=tag.category,
        attributes=json.dumps(tag.attributes),
        caption=tag.caption,
        confidence=tag.confidence,
        embedding=embedding,
        flagged=tag.confidence < 0.85,
        flagged_reason="Low confidence" if tag.confidence < 0.85 else None,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return image.id


def batch_process_images(
    db: Session,
    image_dir: str,
    embedding_fn=None,
) -> dict:
    """
    Batch process all images in a directory.

    Args:
        db: Database session
        image_dir: Directory containing images
        embedding_fn: Optional function to generate embeddings

    Returns:
        dict: Summary of processing (processed, failed, etc.)
    """
    init_gemini()

    image_dir = Path(image_dir)
    if not image_dir.exists():
        raise ValueError(f"Image directory not found: {image_dir}")

    processed = 0
    failed = 0
    results = []

    for image_file in image_dir.glob("*"):
        if image_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        try:
            tag = process_image_file(str(image_file))

            embedding = None
            if embedding_fn:
                embedding = embedding_fn(tag.caption)

            image_id = save_image_record(db, image_file.name, tag, embedding)

            log_gemini_call(
                db,
                call_type="vision_analysis",
                model="gemini-2.0-flash",
                cost_usd=0.001,
                image_id=image_id,
                status="success",
            )

            processed += 1
            results.append({
                "filename": image_file.name,
                "image_id": image_id,
                "status": "success",
            })

        except Exception as e:
            failed += 1
            results.append({
                "filename": image_file.name,
                "status": "failed",
                "error": str(e),
            })

    return {
        "total_processed": processed,
        "total_failed": failed,
        "results": results,
    }
