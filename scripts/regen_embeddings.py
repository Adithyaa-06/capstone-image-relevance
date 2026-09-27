#!/usr/bin/env python
"""Regenerate embeddings for all images and posts with real Gemini API."""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.database import Image, Post
from app.jobs.embedding_batch import generate_embedding
from app.core.cost_tracker import log_gemini_call

db = SessionLocal()

try:
    print("Regenerating image embeddings...")
    images = db.query(Image).all()
    for idx, image in enumerate(images, 1):
        try:
            embedding = generate_embedding(image.caption)
            image.embedding = embedding
            db.commit()

            log_gemini_call(
                db,
                call_type="embedding",
                model="models/gemini-embedding-001",
                cost_usd=0.00002,
                image_id=image.id,
                status="success",
            )

            print(f"  {idx}/{len(images)}: {image.filename} (embedding generated)")
            time.sleep(2)
        except Exception as e:
            print(f"  ERROR: {image.filename} - {str(e)}")
            db.rollback()

    print("\nRegenerating post embeddings...")
    posts = db.query(Post).all()
    for idx, post in enumerate(posts, 1):
        try:
            combined_text = f"{post.title} {post.content}"
            embedding = generate_embedding(combined_text)
            post.embedding = embedding
            db.commit()

            log_gemini_call(
                db,
                call_type="embedding",
                model="models/gemini-embedding-001",
                cost_usd=0.00002,
                post_id=post.id,
                status="success",
            )

            print(f"  {idx}/{len(posts)}: {post.title[:40]}... (embedding generated)")
            time.sleep(2)
        except Exception as e:
            print(f"  ERROR: {post.title} - {str(e)}")
            db.rollback()

    print("\nVerifying embeddings...")
    images_with = db.query(Image).filter(Image.embedding != None).count()
    posts_with = db.query(Post).filter(Post.embedding != None).count()
    print(f"Images with embeddings: {images_with}/{len(images)}")
    print(f"Posts with embeddings: {posts_with}/{len(posts)}")

    sample_image = db.query(Image).filter(Image.embedding != None).first()
    if sample_image:
        print(f"\nSample image: {sample_image.filename}")
        print(f"Embedding dimension: {len(sample_image.embedding)}")
        print(f"First 5 values: {sample_image.embedding[:5]}")

    print("\nDone!")
finally:
    db.close()
