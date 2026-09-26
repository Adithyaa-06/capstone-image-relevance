"""
Seed the database with test images from Unsplash.
Downloads ~50 images and processes them via Gemini vision.

Usage:
    python scripts/seed_images.py
"""

import os
import json
import requests
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.jobs.vision_batch import process_image_file, save_image_record
from app.jobs.embedding_batch import generate_embedding
from app.core.cost_tracker import log_gemini_call


UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY", "")
IMAGE_DIR = Path("data/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_QUERIES = [
    "red fox",
    "wolf",
    "deer",
    "bear",
    "eagle",
    "lion",
    "tiger",
    "elephant",
    "giraffe",
    "zebra",
    "tree",
    "forest",
    "mountain",
    "river",
    "ocean",
]


def download_images_from_unsplash():
    """Download ~50 test images from Unsplash."""
    if not UNSPLASH_API_KEY:
        print("❌ UNSPLASH_API_KEY not set. Skipping Unsplash download.")
        print("   To use this feature, set UNSPLASH_API_KEY in .env")
        return False

    images_downloaded = 0

    for query in SEARCH_QUERIES:
        for page in range(1, 4):
            try:
                url = f"https://api.unsplash.com/search/photos"
                params = {
                    "query": query,
                    "page": page,
                    "per_page": 1,
                    "client_id": UNSPLASH_API_KEY,
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                if not data.get("results"):
                    continue

                photo = data["results"][0]
                download_url = photo["urls"]["regular"]
                filename = f"{query.replace(' ', '_')}_{page}.jpg"
                filepath = IMAGE_DIR / filename

                if filepath.exists():
                    continue

                img_response = requests.get(download_url, timeout=10)
                img_response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(img_response.content)

                images_downloaded += 1
                print(f"✓ Downloaded: {filename}")

            except Exception as e:
                print(f"✗ Failed to download {query} page {page}: {str(e)}")

    print(f"\n📊 Total images downloaded: {images_downloaded}")
    return images_downloaded > 0


def seed_from_existing_images(db: Session):
    """Process existing images in data/images/ directory."""
    processed = 0
    failed = 0

    for image_file in IMAGE_DIR.glob("*"):
        if image_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        try:
            print(f"Processing: {image_file.name}")
            tag = process_image_file(str(image_file))

            embedding = generate_embedding(tag.caption)
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
            print(f"  ✓ Saved as image_id={image_id}")

        except Exception as e:
            failed += 1
            print(f"  ✗ Failed: {str(e)}")

    return processed, failed


def main():
    """Seed the database with test images."""
    print("🌄 FlyRank Image Seeding Pipeline")
    print("=" * 50)

    db = SessionLocal()
    try:
        print("\n📥 Step 1: Download images from Unsplash")
        download_images_from_unsplash()

        print("\n🔍 Step 2: Process existing images with Gemini")
        processed, failed = seed_from_existing_images(db)

        print(f"\n✅ Complete!")
        print(f"   Processed: {processed}")
        print(f"   Failed: {failed}")
        print(f"\n   View results:")
        print(f"   - GET http://localhost:8000/images")
        print(f"   - GET http://localhost:8000/cost-log/summary")

    finally:
        db.close()


if __name__ == "__main__":
    main()
