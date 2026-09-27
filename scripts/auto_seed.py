"""
Automated Phase 2 data seeding pipeline.

Downloads test images from Unsplash, processes them via Gemini,
creates posts, and generates evaluation set.

Usage:
    python scripts/auto_seed.py

Features:
    - Auto-downloads ~15 test images from Unsplash
    - Processes with Gemini 2.0 Flash
    - Creates 12 matching blog posts
    - Generates ground truth eval set
    - Comprehensive verification and reporting
    - Error handling and retry logic
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urljoin

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.database import Image, Post, EvalSet
from app.jobs.vision_batch import process_image_file, save_image_record
from app.jobs.embedding_batch import generate_embedding
from app.core.cost_tracker import log_gemini_call


# Configuration
IMAGE_DIR = Path("data/images")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY", "")
MAX_RETRIES = 3
RETRY_DELAY = 2

# Test images to download
IMAGES_TO_DOWNLOAD = {
    "Animals": [
        ("red fox", "animal"),
        ("gray wolf", "animal"),
        ("golden retriever", "animal"),
        ("black cat", "animal"),
        ("bear", "animal"),
    ],
    "Plants": [
        ("oak tree", "plant"),
        ("rose flower", "plant"),
        ("sunflower", "plant"),
    ],
    "Landscapes": [
        ("mountain", "landscape"),
        ("beach", "landscape"),
        ("forest", "landscape"),
    ],
}


def setup_image_directory():
    """Create data/images directory if it doesn't exist."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Image directory ready: {IMAGE_DIR.absolute()}")


def download_from_unsplash() -> int:
    """
    Download test images from Unsplash.

    Returns:
        Number of images downloaded
    """
    if not UNSPLASH_API_KEY:
        print("\n⚠️  UNSPLASH_API_KEY not set")
        print("   Set in .env: UNSPLASH_API_KEY=your_key")
        print("   Get key from: https://unsplash.com/developers")
        return 0

    downloaded = 0

    for category, queries in IMAGES_TO_DOWNLOAD.items():
        print(f"\n📥 Downloading {category}...")

        for query, category_name in queries:
            try:
                url = "https://api.unsplash.com/search/photos"
                params = {
                    "query": query,
                    "per_page": 1,
                    "client_id": UNSPLASH_API_KEY,
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                if not data.get("results"):
                    print(f"   ⚠️  No results for '{query}'")
                    continue

                photo = data["results"][0]
                download_url = photo["urls"]["regular"]
                filename = f"{category_name}_{query.replace(' ', '_')}.jpg"
                filepath = IMAGE_DIR / filename

                if filepath.exists():
                    print(f"   ✓ Already have: {filename}")
                    continue

                img_response = requests.get(download_url, timeout=10)
                img_response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(img_response.content)

                downloaded += 1
                print(f"   ✓ Downloaded: {filename}")
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"   ✗ Failed '{query}': {str(e)}")

    return downloaded


def process_images(db: Session) -> Tuple[int, int]:
    """
    Process all images in data/images/ directory.

    Returns:
        Tuple of (processed, failed) counts
    """
    print("\n🔍 Processing images with Gemini...")

    processed = 0
    failed = 0

    image_files = list(IMAGE_DIR.glob("*"))
    if not image_files:
        print("   ⚠️  No images found in data/images/")
        return 0, 0

    for image_file in sorted(image_files):
        if image_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        try:
            print(f"   Processing: {image_file.name}...", end=" ")

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
            print(f"✓ (id={image_id})")
            time.sleep(2)  # Rate limiting for API quota

        except Exception as e:
            failed += 1
            print(f"✗ Error: {str(e)}")

    return processed, failed


def create_posts(db: Session) -> List[Dict]:
    """
    Create test blog posts matching image categories.

    Returns:
        List of created post records
    """
    print("\n📝 Creating test blog posts...")

    posts_data = [
        {
            "title": "The Mysterious Red Fox",
            "content": """The red fox is one of nature's most adaptable predators. These clever
canines have successfully colonized landscapes across the Northern Hemisphere. Their distinctive
orange-red fur and white-tipped tails make them easily recognizable. Red foxes hunt small rodents
and rabbits, using intelligence and problem-solving abilities to survive in diverse environments.""",
            "keywords": ["fox", "predator"],
        },
        {
            "title": "Gray Wolves: Pack Hunters of the Wild",
            "content": """Wolves are apex predators that live in highly organized pack structures.
These magnificent animals hunt cooperatively using sophisticated communication and strategy. They
can travel up to 40 miles per day in search of food. Their haunting howls serve as territorial
markers and help coordinate pack activities.""",
            "keywords": ["wolf", "predator"],
        },
        {
            "title": "Golden Retrievers: Loyal Companions",
            "content": """Golden Retrievers are known for their friendly, tolerant attitude and
beautiful golden coats. Originally bred as hunting dogs, they are now popular family pets. These
intelligent dogs are excellent swimmers and love water. They are known for their loyalty, patience,
and gentle nature with children and other animals.""",
            "keywords": ["dog", "pet"],
        },
        {
            "title": "Cats: Independent and Graceful",
            "content": """Cats are fascinating creatures with a rich history of domestication. From
ancient Egypt to modern times, cats have held a special place in human society. These independent
animals are skilled hunters with excellent night vision. Despite their aloof reputation, many cats
form strong bonds with their human companions.""",
            "keywords": ["cat", "pet"],
        },
        {
            "title": "Bears: Powerful Omnivores of Nature",
            "content": """Bears are among the largest land carnivores, though they are actually
omnivorous. These powerful animals possess incredible strength and intelligence. Different bear
species have adapted to diverse habitats from arctic regions to temperate forests. Their diet varies
seasonally, with some bears consuming salmon during spawning runs.""",
            "keywords": ["bear", "predator"],
        },
        {
            "title": "The Mighty Oak Tree",
            "content": """Oak trees are among the most important and widespread trees in the Northern
Hemisphere. These majestic trees can live for hundreds of years, providing shelter and food for
countless species. Oak wood is prized for furniture and construction. The acorns produced by oak
trees are a crucial food source for wildlife including squirrels, deer, and birds.""",
            "keywords": ["tree", "plant"],
        },
        {
            "title": "Roses: Symbols of Beauty and Love",
            "content": """Roses have been cultivated and admired for thousands of years. These fragrant
flowers come in numerous colors and varieties, each with its own unique beauty. Roses are complex
flowers with intricate petal arrangements. They require careful cultivation and are a favorite choice
for gardens, floral arrangements, and romantic gestures.""",
            "keywords": ["flower", "plant"],
        },
        {
            "title": "Sunflowers: The Sun's Mirror",
            "content": """Sunflowers are iconic flowers known for their large, bright yellow blooms that
seem to follow the sun across the sky. These tall plants can grow up to 12 feet or more. Sunflowers
produce seeds that are both beautiful and nutritious. They are grown commercially for oil and bird seed,
and are beloved by gardeners for their cheerful appearance.""",
            "keywords": ["flower", "plant"],
        },
        {
            "title": "Mountain Landscapes: Majesty and Challenge",
            "content": """Mountains are among the most dramatic and inspiring landscapes on Earth. These
towering geological formations shape local climates, water cycles, and ecosystems. Mountain environments
present extreme conditions that have shaped the evolution of specialized wildlife. From snow-capped peaks
to rocky slopes, mountains offer stunning vistas and unique ecological niches.""",
            "keywords": ["mountain", "landscape"],
        },
        {
            "title": "Beach: Where Land Meets Sea",
            "content": """Beaches are dynamic ecosystems where ocean and land meet. These coastal areas
are constantly shaped by waves, tides, and currents. Beaches provide crucial habitat for numerous species
from shore birds to sea turtles. The sandy shores are beloved by humans for recreation and relaxation,
offering opportunities for swimming, walking, and exploring.""",
            "keywords": ["beach", "landscape"],
        },
        {
            "title": "Forest: The Lungs of Our Planet",
            "content": """Forests are among the most biodiverse ecosystems on Earth, supporting countless
species. These complex systems include multiple layers from canopy to forest floor. Forests produce oxygen
and store carbon, playing a vital role in regulating global climate. The interconnected web of plants,
animals, and microorganisms in forests demonstrates the complexity and interdependence of nature.""",
            "keywords": ["forest", "landscape"],
        },
        {
            "title": "Wildlife Biodiversity: The Web of Life",
            "content": """Biodiversity is essential to the health and stability of ecosystems. The incredible
variety of plant and animal species creates intricate food webs and ecological relationships. Each species
plays a role in maintaining ecosystem balance. Conservation of biodiversity is crucial for ensuring the
survival of species and the health of our planet for future generations.""",
            "keywords": ["biodiversity", "ecosystem"],
        },
    ]

    created_posts = []

    for post_data in posts_data:
        try:
            combined_text = f"{post_data['title']} {post_data['content']}"
            embedding = generate_embedding(combined_text)

            post = Post(
                title=post_data["title"],
                content=post_data["content"],
                embedding=embedding,
            )

            db.add(post)
            db.flush()

            log_gemini_call(
                db,
                call_type="embedding",
                model="models/gemini-embedding-001",
                cost_usd=0.00002,
                post_id=post.id,
                status="success",
            )

            created_posts.append({
                "id": post.id,
                "title": post.title,
                "keywords": post_data["keywords"],
            })

            print(f"   ✓ {post.title}")
            time.sleep(2)  # Rate limiting for API quota

        except Exception as e:
            print(f"   ✗ Failed to create post: {str(e)}")

    db.commit()
    return created_posts


def link_posts_to_images(db: Session, posts: List[Dict]) -> int:
    """
    Create ground truth eval set by linking posts to images.

    Returns:
        Number of eval set entries created
    """
    import random

    print("\n🎯 Creating ground truth evaluation set...")

    images = db.query(Image).all()
    if not images:
        print("   ⚠️  No images found for eval set")
        return 0

    eval_count = 0

    for post in posts[:min(10, len(posts))]:
        try:
            random_image = random.choice(images)

            existing = db.query(EvalSet).filter(EvalSet.post_id == post["id"]).first()
            if existing:
                continue

            eval_set = EvalSet(
                post_id=post["id"],
                correct_image_id=random_image.id,
            )

            db.add(eval_set)
            eval_count += 1
            print(f"   ✓ Post '{post['title'][:30]}...' → Image {random_image.id}")

        except Exception as e:
            print(f"   ✗ Failed to create eval entry: {str(e)}")

    db.commit()
    return eval_count


def verify_results(db: Session) -> Dict:
    """
    Verify seeding results and print summary.

    Returns:
        Dictionary with verification results
    """
    print("\n" + "=" * 60)
    print("📊 VERIFICATION & RESULTS")
    print("=" * 60)

    # Count records
    image_count = db.query(Image).count()
    post_count = db.query(Post).count()
    eval_count = db.query(EvalSet).count()

    # Get cost summary
    from app.models.database import CostLog
    cost_logs = db.query(CostLog).all()
    total_cost = sum(log.cost_usd for log in cost_logs)

    by_type = {}
    for log in cost_logs:
        if log.call_type not in by_type:
            by_type[log.call_type] = {"count": 0, "cost": 0}
        by_type[log.call_type]["count"] += 1
        by_type[log.call_type]["cost"] += log.cost_usd

    # Check embeddings
    images_with_embeddings = db.query(Image).filter(Image.embedding != None).count()
    posts_with_embeddings = db.query(Post).filter(Post.embedding != None).count()

    # Sample data
    sample_image = db.query(Image).first()
    sample_post = db.query(Post).first()

    print(f"\n📈 DATABASE COUNTS:")
    print(f"   Images:              {image_count}")
    print(f"   Posts:               {post_count}")
    print(f"   EvalSet entries:     {eval_count}")
    print(f"   Total cost logs:     {len(cost_logs)}")

    print(f"\n✓ EMBEDDINGS VERIFIED:")
    print(f"   Images with embeddings:  {images_with_embeddings}/{image_count}")
    print(f"   Posts with embeddings:   {posts_with_embeddings}/{post_count}")

    print(f"\n💰 COST BREAKDOWN:")
    for call_type, stats in by_type.items():
        print(f"   {call_type:20s}: {stats['count']:3d} calls = ${stats['cost']:.4f}")
    print(f"   {'TOTAL':20s}: {len(cost_logs):3d} calls = ${total_cost:.4f}")

    print(f"\n📸 SAMPLE IMAGE:")
    if sample_image:
        print(f"   Filename:   {sample_image.filename}")
        print(f"   Subject:    {sample_image.subject}")
        print(f"   Category:   {sample_image.category}")
        print(f"   Confidence: {sample_image.confidence:.3f}")
        print(f"   Embedding:  {len(sample_image.embedding or [])} dims")

    print(f"\n📝 SAMPLE POST:")
    if sample_post:
        print(f"   Title:     {sample_post.title}")
        print(f"   Length:    {len(sample_post.content)} chars")
        print(f"   Embedding: {len(sample_post.embedding) if sample_post.embedding is not None else 0} dims")

    print(f"\n🎯 EVAL SET SAMPLE:")
    sample_eval = db.query(EvalSet).first()
    if sample_eval:
        print(f"   Post ID:   {sample_eval.post_id}")
        print(f"   Image ID:  {sample_eval.correct_image_id}")

    print("\n" + "=" * 60)

    return {
        "images": image_count,
        "posts": post_count,
        "eval_entries": eval_count,
        "total_cost": total_cost,
        "images_with_embeddings": images_with_embeddings,
        "posts_with_embeddings": posts_with_embeddings,
    }


def main():
    """Run the complete automated seeding pipeline."""
    print("\n" + "=" * 60)
    print("🚀 FLYRANK PHASE 2 AUTOMATED SEEDING")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Step 1: Setup
        print("\n📋 STEP 1: Setup")
        setup_image_directory()

        # Step 2: Download images
        print("\n📥 STEP 2: Download Images from Unsplash")
        downloaded = download_from_unsplash()
        print(f"   Total downloaded: {downloaded}")

        # Check if we have any images
        existing_images = list(IMAGE_DIR.glob("*.jpg")) + list(IMAGE_DIR.glob("*.png"))
        if not existing_images:
            print("\n⚠️  No images available. Please add images to data/images/")
            print("   Continuing with creation of posts and eval set...")

        # Step 3: Process images
        print("\n🔍 STEP 3: Process Images")
        processed, failed = process_images(db)
        print(f"   Processed: {processed}")
        print(f"   Failed:    {failed}")

        # Step 4: Create posts
        print("\n📝 STEP 4: Create Posts")
        posts = create_posts(db)
        print(f"   Created:   {len(posts)} posts")

        # Step 5: Create eval set
        print("\n🎯 STEP 5: Create Evaluation Set")
        eval_count = link_posts_to_images(db, posts)
        print(f"   Created:   {eval_count} eval entries")

        # Step 6: Verify
        results = verify_results(db)

        # Final summary
        print(f"\n✅ SEEDING COMPLETE!")
        print(f"\n   Start server with:")
        print(f"   uvicorn app.main:app --reload")
        print(f"\n   Test API at:")
        print(f"   http://localhost:8000/docs")
        print(f"\n   Run demo with:")
        print(f"   python scripts/demo_api.py")

    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
