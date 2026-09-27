#!/usr/bin/env python
"""Clear all embeddings from database to regenerate with real API."""
from app.core.database import SessionLocal
from app.models.database import Image, Post

db = SessionLocal()
try:
    image_count = db.query(Image).update({"embedding": None})
    post_count = db.query(Post).update({"embedding": None})
    db.commit()
    print(f"Cleared embeddings: {image_count} images, {post_count} posts")
finally:
    db.close()
