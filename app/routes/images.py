"""
Image management routes.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from sqlalchemy.orm import Session
from typing import List
import json
from app.models.database import Image
from app.models.schemas import ImageRecord
from app.jobs.vision_batch import process_image_file, save_image_record, generate_embedding
from app.core.database import get_db
import tempfile
import os

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/batch-process")
async def batch_process_images(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Process batch of image files.
    Extracts metadata via Gemini Flash vision model.
    """
    results = []

    for file in files:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp.flush()
                tmp_path = tmp.name

            try:
                tag = process_image_file(tmp_path)
                embedding = generate_embedding(tag.caption)
                image_id = save_image_record(db, file.filename, tag, embedding)

                results.append({
                    "filename": file.filename,
                    "image_id": image_id,
                    "status": "success",
                    "subject": tag.subject,
                })
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e),
            })

    return {
        "total": len(files),
        "processed": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results,
    }


@router.get("/{image_id}", response_model=ImageRecord)
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    """Get image record by ID."""
    image = db.query(Image).filter(Image.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return ImageRecord(
        id=image.id,
        filename=image.filename,
        subject=image.subject,
        category=image.category,
        attributes=json.loads(image.attributes),
        caption=image.caption,
        confidence=image.confidence,
        flagged=image.flagged,
        flagged_reason=image.flagged_reason,
        embedding=image.embedding,
        created_at=image.created_at.isoformat(),
    )


@router.get("/", response_model=List[ImageRecord])
async def list_images(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all images with pagination."""
    images = db.query(Image).offset(skip).limit(limit).all()

    return [
        ImageRecord(
            id=img.id,
            filename=img.filename,
            subject=img.subject,
            category=img.category,
            attributes=json.loads(img.attributes),
            caption=img.caption,
            confidence=img.confidence,
            flagged=img.flagged,
            flagged_reason=img.flagged_reason,
            embedding=img.embedding,
            created_at=img.created_at.isoformat(),
        )
        for img in images
    ]
