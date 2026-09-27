#!/usr/bin/env python
"""Test similarity scores between specific posts and images."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.database import Image, Post
import numpy as np

def cosine_similarity(vec_a, vec_b):
    """Calculate cosine similarity between two vectors."""
    vec_a = np.array(vec_a, dtype=float)
    vec_b = np.array(vec_b, dtype=float)
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))

db = SessionLocal()
try:
    print("Wolf-on-Fox Rejection Test")
    print("=" * 50)

    # Get wolf post and fox images
    wolf_post = db.query(Post).filter(Post.id == 5).first()  # Gray Wolves post
    fox_image_1 = db.query(Image).filter(Image.id == 1).first()  # fox1.jpg
    fox_image_2 = db.query(Image).filter(Image.id == 2).first()  # fox2.jpg

    print(f"\nWolf Post: '{wolf_post.title}'")
    print(f"Fox Image 1: {fox_image_1.filename} (id={fox_image_1.id}, confidence={fox_image_1.confidence:.3f})")
    print(f"Fox Image 2: {fox_image_2.filename} (id={fox_image_2.id}, confidence={fox_image_2.confidence:.3f})")

    sim_wolf_to_fox1 = cosine_similarity(wolf_post.embedding, fox_image_1.embedding)
    sim_wolf_to_fox2 = cosine_similarity(wolf_post.embedding, fox_image_2.embedding)

    print(f"\nSimilarity: Wolf Post to Fox1: {sim_wolf_to_fox1:.4f}")
    print(f"Similarity: Wolf Post to Fox2: {sim_wolf_to_fox2:.4f}")

    # Check if they would pass the guard
    THRESHOLD = 0.75
    print(f"\nGuard Threshold: {THRESHOLD}")
    print(f"Wolf->Fox1 passes guard? {sim_wolf_to_fox1 >= THRESHOLD}")
    print(f"Wolf->Fox2 passes guard? {sim_wolf_to_fox2 >= THRESHOLD}")

    print("\n" + "=" * 50)
    print("Fox Post to Both Fox Images")
    print("=" * 50)

    fox_post = db.query(Post).filter(Post.id == 1).first()  # Red Fox post
    print(f"\nFox Post: '{fox_post.title}'")

    sim_fox_to_fox1 = cosine_similarity(fox_post.embedding, fox_image_1.embedding)
    sim_fox_to_fox2 = cosine_similarity(fox_post.embedding, fox_image_2.embedding)

    print(f"Similarity: Fox Post to Fox1: {sim_fox_to_fox1:.4f}")
    print(f"Similarity: Fox Post to Fox2: {sim_fox_to_fox2:.4f}")

    print(f"\nFox->Fox1 passes guard? {sim_fox_to_fox1 >= THRESHOLD}")
    print(f"Fox->Fox2 passes guard? {sim_fox_to_fox2 >= THRESHOLD}")

finally:
    db.close()
