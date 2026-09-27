"""
Batch generate embeddings for image captions and posts via Gemini.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import Session
from app.models.database import Image, Post
from app.core.cost_tracker import log_gemini_call

load_dotenv()  # Load environment variables from .env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def init_gemini():
    """Initialize Gemini API with key from environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    genai.configure(api_key=api_key)


def generate_embedding(text: str) -> list:
    try:
        result = genai.embed_content(
            model="text-embedding-004",
            content=text,
        )
        return result["embedding"]
    except Exception as e:
        raise ValueError(f"Embedding generation failed: {str(e)}")

def embed_image_captions(db: Session) -> dict:
    """
    Generate embeddings for all image captions.

    Args:
        db: Database session

    Returns:
        dict: Summary of embedding generation
    """
    init_gemini()

    images = db.query(Image).filter(Image.embedding == None).all()
    processed = 0
    failed = 0

    for image in images:
        try:
            embedding = generate_embedding(image.caption)
            image.embedding = embedding
            db.commit()

            log_gemini_call(
                db,
                call_type="embedding",
                model="text-embedding-004",
                cost_usd=0.00002,
                image_id=image.id,
                status="success",
            )

            processed += 1
        except Exception as e:
            failed += 1
            db.rollback()

    return {
        "total_processed": processed,
        "total_failed": failed,
    }


def embed_posts(db: Session) -> dict:
    """
    Generate embeddings for all posts.

    Args:
        db: Database session

    Returns:
        dict: Summary of embedding generation
    """
    init_gemini()

    posts = db.query(Post).filter(Post.embedding == None).all()
    processed = 0
    failed = 0

    for post in posts:
        try:
            combined_text = f"{post.title} {post.content}"
            embedding = generate_embedding(combined_text)
            post.embedding = embedding
            db.commit()

            log_gemini_call(
                db,
                call_type="embedding",
                model="text-embedding-004",
                cost_usd=0.00002,
                post_id=post.id,
                status="success",
            )

            processed += 1
        except Exception as e:
            failed += 1
            db.rollback()

    return {
        "total_processed": processed,
        "total_failed": failed,
    }