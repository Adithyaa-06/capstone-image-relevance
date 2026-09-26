# FlyRank Setup Guide

Complete step-by-step guide to set up and run the FlyRank capstone project.

## Prerequisites

- Python 3.9+
- PostgreSQL 13+ installed and running
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com))
- Optional: Unsplash API key for downloading test images

## Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd capstone-image-relevance

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure PostgreSQL

```bash
# Create database
createdb flyrank

# Connect to the database and enable pgvector
psql flyrank

# Inside psql, run:
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

Verify pgvector is installed:
```bash
psql flyrank -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

## Step 3: Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings
# Minimum required:
# GEMINI_API_KEY=your_api_key_here
# DATABASE_URL=postgresql://user:password@localhost:5432/flyrank
```

**Important**: Update `DATABASE_URL` to match your PostgreSQL setup.

Example for local PostgreSQL with default user:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/flyrank
```

## Step 4: Initialize Database

```bash
# Create all database tables
python scripts/init_db.py
```

Expected output:
```
🗄️  FlyRank Database Initialization
==================================================

📋 Creating database tables...
✅ Database initialized successfully!

   Tables created:
   - images
   - posts
   - suggestions
   - cost_logs
   - eval_set
```

## Step 5: Populate with Test Data

### Option A: Seed with Unsplash Images (requires API key)

```bash
# Add UNSPLASH_API_KEY to .env
# UNSPLASH_API_KEY=your_unsplash_key

python scripts/seed_images.py
python scripts/seed_posts.py
```

### Option B: Manual Image Setup (no API key needed)

1. Create a `data/images/` directory:
```bash
mkdir -p data/images
```

2. Add your test images (JPG or PNG) to `data/images/`

3. Run the seeding script:
```bash
python scripts/seed_images.py
python scripts/seed_posts.py
```

## Step 6: Start the Server

```bash
# Run the FastAPI server
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application started, database initialized
```

## Step 7: Test the API

### In a new terminal:

```bash
# Run the demo script
python scripts/demo_api.py
```

### Or use the interactive API docs:

Open your browser to: **http://localhost:8000/docs**

This gives you an interactive Swagger UI to test all endpoints.

## Step 8: Run Tests

```bash
# Run pytest
pytest tests/ -v

# Or run specific test file
pytest tests/test_guard.py -v
```

## Common Endpoints to Try

### List all images
```bash
curl http://localhost:8000/images
```

### List all posts
```bash
curl http://localhost:8000/posts
```

### Get image suggestions for a post
```bash
curl http://localhost:8000/posts/1/images
```

### Get evaluation precision
```bash
curl http://localhost:8000/eval/precision
```

### Get cost summary
```bash
curl http://localhost:8000/cost-log/summary
```

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server: No such file or directory
```

**Solution**: Make sure PostgreSQL is running:
```bash
# macOS with Homebrew
brew services start postgresql

# Linux with systemd
sudo systemctl start postgresql

# Windows
# Start PostgreSQL service from Services
```

### pgvector Extension Not Found
```
ERROR: permission denied to create extension "vector"
```

**Solution**: Run pgvector creation as superuser:
```bash
psql -U postgres flyrank -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Gemini API Errors
```
google.api_core.exceptions.InvalidArgument: Vision model returned invalid response
```

**Solution**: 
1. Verify GEMINI_API_KEY is set correctly
2. Check API quota at [Google Cloud Console](https://console.cloud.google.com)
3. Make sure you have vision API enabled

### Module Import Error
```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Make sure you're running from the project root:
```bash
cd capstone-image-relevance
python scripts/seed_images.py
```

## Project Structure

```
capstone-image-relevance/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── database.py        # Database setup
│   │   ├── guard.py           # Mismatch guard logic
│   │   └── cost_tracker.py    # Cost logging
│   ├── models/
│   │   ├── database.py        # SQLAlchemy models
│   │   └── schemas.py         # Pydantic schemas
│   ├── routes/
│   │   ├── images.py          # Image endpoints
│   │   ├── posts.py           # Post endpoints
│   │   ├── suggestions.py     # Suggestion endpoints
│   │   ├── eval_routes.py     # Evaluation endpoints
│   │   └── cost_routes.py     # Cost endpoints
│   └── jobs/
│       ├── vision_batch.py    # Image processing
│       └── embedding_batch.py # Embedding generation
├── scripts/
│   ├── init_db.py             # Database initialization
│   ├── seed_images.py         # Image seeding
│   ├── seed_posts.py          # Post seeding
│   └── demo_api.py            # API testing
├── tests/
│   ├── test_guard.py          # Guard tests
│   └── test_schemas.py        # Schema validation tests
├── data/
│   └── images/                # Test images directory
├── .env                       # Environment variables (git ignored)
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── SETUP.md                  # Setup guide (this file)
├── capstone.yaml             # API manifest
├── BUILDLOG.md              # Build documentation
└── EVIDENCE.md              # Requirements traceability
```

## Workflow Example

1. **Upload Images**
   ```bash
   # Place images in data/images/
   # Run the seed script
   python scripts/seed_images.py
   ```

2. **Create Posts**
   ```bash
   python scripts/seed_posts.py
   ```

3. **Find Matches**
   ```bash
   curl http://localhost:8000/posts/1/images
   ```

4. **Approve/Reject**
   ```bash
   curl -X POST http://localhost:8000/posts/suggestions/1/approve
   curl -X POST http://localhost:8000/posts/suggestions/2/reject \
     -H "Content-Type: application/json" \
     -d '{"reason": "Image does not match content"}'
   ```

5. **Check Metrics**
   ```bash
   curl http://localhost:8000/eval/precision
   curl http://localhost:8000/cost-log/summary
   ```

## Development Tips

### Enable Debug Logging
```python
# In app/main.py or any route:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test a Single Endpoint
```bash
# Using Python requests
python -c "
import requests
r = requests.get('http://localhost:8000/health')
print(r.json())
"
```

### Clear Database
```bash
psql flyrank -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python scripts/init_db.py
```

### Monitor Costs in Real-Time
```bash
# Run in a loop
while true; do
  curl -s http://localhost:8000/cost-log/summary | python -m json.tool
  sleep 5
done
```

## Performance Tuning

### Database Connection Pool
Edit `app/core/database.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Number of connections
    max_overflow=10,     # Extra connections when needed
    pool_recycle=3600,   # Recycle connections every hour
)
```

### Batch Processing
Adjust batch sizes in:
- `scripts/seed_images.py`
- `scripts/seed_posts.py`

### API Rate Limiting (optional)
Add slowapi to requirements.txt and configure rate limits.

## Next Steps

1. Review the [README.md](README.md) for architecture details
2. Check [EVIDENCE.md](EVIDENCE.md) for requirements traceability
3. Run the test suite: `pytest tests/`
4. Customize guard thresholds in `app/core/guard.py`
5. Add more test images to `data/images/`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review error messages in the server logs
3. Check [README.md](README.md) for architecture questions
4. Review the code comments in individual files

Good luck with your FlyRank capstone! 🎯
