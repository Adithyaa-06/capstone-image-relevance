"""
Post management routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models.database import Post
from app.models.schemas import PostRecord
from app.jobs.embedding_batch import generate_embedding
from app.core.database import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("")
async def create_post(
    title: str,
    content: str,
    db: Session = Depends(get_db),
):
    """Create a new post and generate embedding."""
    try:
        combined_text = f"{title} {content}"
        embedding = generate_embedding(combined_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Embedding generation failed: {str(e)}")

    post = Post(
        title=title,
        content=content,
        embedding=embedding,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostRecord(
        id=post.id,
        title=post.title,
        content=post.content,
        embedding=post.embedding,
        created_at=post.created_at.isoformat(),
    )


@router.get("/{post_id}", response_model=PostRecord)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get post by ID."""
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return PostRecord(
        id=post.id,
        title=post.title,
        content=post.content,
        embedding=post.embedding,
        created_at=post.created_at.isoformat(),
    )


@router.get("", response_model=List[PostRecord])
async def list_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all posts with pagination."""
    posts = db.query(Post).offset(skip).limit(limit).all()

    return [
        PostRecord(
            id=p.id,
            title=p.title,
            content=p.content,
            embedding=p.embedding,
            created_at=p.created_at.isoformat(),
        )
        for p in posts
    ]
