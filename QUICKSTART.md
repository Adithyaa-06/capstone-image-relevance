# FlyRank Quick Start Guide

Get FlyRank up and running in 5 minutes with automated seeding.

## Prerequisites
- Python 3.9+
- PostgreSQL installed and running
- Gemini API key (get from https://aistudio.google.com)
- Optional: Unsplash API key (get from https://unsplash.com/developers)

## One-Command Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database
createdb flyrank
psql flyrank -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run automated seeding
python scripts/auto_seed.py

# 5. Start server
uvicorn app.main:app --reload
```

That's it! Your FlyRank instance is ready.

## What auto_seed.py Does

The automated seeding script:

1. **Downloads ~15 test images** from Unsplash (if API key provided)
   - Animals: fox, wolf, dog, cat, bear
   - Plants: oak tree, rose, sunflower
   - Landscapes: mountain, beach, forest

2. **Processes images** with Gemini 2.0 Flash
   - Extracts subject, category, attributes, caption, confidence
   - Validates with Pydantic
   - Saves with embeddings

3. **Creates 12 blog posts** matching image categories
   - Embeds each post automatically
   - Creates ground truth eval set
   - Links posts to images for evaluation

4. **Verifies results**
   - Prints database counts
   - Shows cost breakdown
   - Confirms all embeddings stored
   - Displays sample data

## Expected Output

```
============================================================
🚀 FLYRANK PHASE 2 AUTOMATED SEEDING
============================================================

📋 STEP 1: Setup
✓ Image directory ready: data/images

📥 STEP 2: Download Images from Unsplash
📥 Downloading Animals...
   ✓ Downloaded: animal_red_fox.jpg
   ✓ Downloaded: animal_gray_wolf.jpg
   ...

🔍 STEP 3: Process Images
   Processing: animal_red_fox.jpg... ✓ (id=1)
   Processing: animal_gray_wolf.jpg... ✓ (id=2)
   ...

📝 STEP 4: Create Posts
   ✓ The Mysterious Red Fox
   ✓ Gray Wolves: Pack Hunters...
   ...

🎯 STEP 5: Create Evaluation Set
   ✓ Post 'The Mysterious Red Fox'... → Image 3
   ...

============================================================
📊 VERIFICATION & RESULTS
============================================================

📈 DATABASE COUNTS:
   Images:              15
   Posts:               12
   EvalSet entries:     10
   Total cost logs:     27

✓ EMBEDDINGS VERIFIED:
   Images with embeddings:  15/15
   Posts with embeddings:   12/12

💰 COST BREAKDOWN:
   vision_analysis      : 15 calls = $0.0150
   embedding            : 27 calls = $0.0005
   TOTAL                : 42 calls = $0.0155

✅ SEEDING COMPLETE!
```

## Test the API

### Option 1: Interactive Docs (Recommended)
Open browser: **http://localhost:8000/docs**

Swagger UI lets you test all endpoints interactively.

### Option 2: Demo Script
```bash
python scripts/demo_api.py
```

### Option 3: Manual curl
```bash
# Health check
curl http://localhost:8000/health

# List images
curl http://localhost:8000/images | python -m json.tool

# List posts
curl http://localhost:8000/posts | python -m json.tool

# Get suggestions for post 1
curl http://localhost:8000/posts/1/images | python -m json.tool

# Check precision
curl http://localhost:8000/eval/precision | python -m json.tool

# View costs
curl http://localhost:8000/cost-log/summary | python -m json.tool
```

## Common Issues

### Error: "UNSPLASH_API_KEY not set"
This is expected if you don't have an Unsplash key. The script will skip image download and you can manually add images to `data/images/`.

**Solution:**
```bash
# Option 1: Set the key
export UNSPLASH_API_KEY=your_key_here
python scripts/auto_seed.py

# Option 2: Download images manually
mkdir -p data/images
# Place your JPG/PNG files in data/images/
python scripts/auto_seed.py
```

### Error: "Connection refused" from PostgreSQL
PostgreSQL is not running.

**Solution:**
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Windows
# Start PostgreSQL service from Services app
```

### Error: "permission denied to create extension"
PostgreSQL not run with proper permissions.

**Solution:**
```bash
# Run as superuser
psql -U postgres flyrank -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Error: "could not translate host name"
Database connection string incorrect.

**Solution:**
1. Check DATABASE_URL in .env
2. Make sure PostgreSQL is running
3. Verify database exists: `psql -l | grep flyrank`

### Error: "GEMINI_API_KEY is invalid"
API key not set or incorrect.

**Solution:**
1. Get key from https://aistudio.google.com
2. Set in .env: `GEMINI_API_KEY=your_key`
3. Check for trailing whitespace

## After Seeding

### View all images
```bash
curl http://localhost:8000/images?limit=100
```

### View all posts
```bash
curl http://localhost:8000/posts?limit=100
```

### Check evaluation metrics
```bash
curl http://localhost:8000/eval/precision
```

### Monitor costs
```bash
curl http://localhost:8000/cost-log/summary
```

### Get suggestions for a specific post
```bash
# For post ID 1
curl http://localhost:8000/posts/1/images
```

### Approve a suggestion
```bash
curl -X POST http://localhost:8000/posts/suggestions/1/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Great match!"}'
```

### Reject a suggestion
```bash
curl -X POST http://localhost:8000/posts/suggestions/2/reject \
  -H "Content-Type: application/json" \
  -d '{"reason": "Image does not match the content theme"}'
```

## Project Structure After Seeding

```
capstone-image-relevance/
├── data/
│   └── images/
│       ├── animal_red_fox.jpg
│       ├── animal_gray_wolf.jpg
│       ├── plant_oak_tree.jpg
│       └── ...
├── app/
│   ├── main.py                 (FastAPI app)
│   ├── core/                   (guard, cost tracker, database)
│   ├── models/                 (SQLAlchemy + Pydantic)
│   ├── routes/                 (API endpoints)
│   └── jobs/                   (vision & embedding processors)
├── scripts/
│   ├── auto_seed.py           (⭐ Use this!)
│   ├── seed_images.py
│   ├── seed_posts.py
│   ├── init_db.py
│   └── demo_api.py
├── .env                        (API keys & DB URL)
├── README.md                   (Full documentation)
└── SETUP.md                    (Detailed setup guide)
```

## Database After Seeding

**Images Table** (15 rows):
- Filename, subject, category, attributes, caption
- Confidence score (0-1)
- 768-dimensional embedding vector
- Auto-flagged if confidence < 0.85

**Posts Table** (12 rows):
- Title, content (500-800 chars)
- 768-dimensional embedding vector

**Suggestions Table** (auto-generated):
- Post-to-image matches
- Similarity scores
- Guard decision (approved/rejected)

**CostLog Table** (27+ rows):
- All API calls logged
- Model, cost, timestamp
- Costs tracked by call type

**EvalSet Table** (10 rows):
- Ground truth post-to-image mappings
- Used for precision evaluation

## Next Steps

1. **Explore the API**: Open http://localhost:8000/docs
2. **Run the demo**: `python scripts/demo_api.py`
3. **Review documentation**: See [README.md](README.md)
4. **Check costs**: `curl http://localhost:8000/cost-log/summary`
5. **Test suggestions**: Get matches for different posts
6. **Measure precision**: Check `http://localhost:8000/eval/precision`

## Cost Summary

Automated seeding of 15 images + 12 posts costs approximately:

```
Vision analysis (15 images)  : 15 × $0.001 = $0.015
Embeddings (27 texts)        : 27 × $0.00002 = $0.0005
Total                        : ~$0.0155
```

All costs are logged and queryable via `/cost-log/summary`.

## Need Help?

1. Check [SETUP.md](SETUP.md) for detailed setup instructions
2. Review [EVIDENCE.md](EVIDENCE.md) for requirements traceability
3. See [README.md](README.md) for architecture details
4. Check logs in server terminal for error messages

---

**Happy building!** 🎯

For questions or issues: Review the troubleshooting section in [SETUP.md](SETUP.md)
