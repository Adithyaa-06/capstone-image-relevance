# FlyRank: AI Image Understanding & Content Matching Engine

A FastAPI backend for intelligent image understanding and semantic content matching using Google's Gemini models.

## Architecture

### Tech Stack
- **Backend**: FastAPI + Uvicorn
- **Database**: PostgreSQL + pgvector
- **Vision Model**: Google Gemini 3.8 Flash
- **Embeddings**:  Google Gemini Embedding (`gemini-embedding-001`, 768-dim)
- **Language**: Python 3.9+

### Core Components

#### 1. Database Models (app/models/database.py)
- **Image**: filename, subject, category, attributes, caption, confidence, embedding, flagged status
- **Post**: title, content, embedding
- **Suggestion**: post-to-image match with similarity score, guard decision, and approval status
- **CostLog**: tracks all Gemini API calls with costs
- **EvalSet**: ground truth post-to-image mappings for precision evaluation

#### 2. Core Modules

**app/core/guard.py** - Mismatch Guard
- Rejects low-confidence matches based on thresholds:
  - Image confidence < 0.85
  - Similarity score < 0.75
  - Semantic mismatch detection

**app/core/cost_tracker.py** - Cost Management
- Logs every Gemini API call with:
  - Call type (vision_analysis, embedding)
  - Model used
  - Cost in USD
  - Timestamp and status

**app/core/database.py** - Database Setup
- PostgreSQL connection with SQLAlchemy ORM
- pgvector for semantic vector operations
- Session management

#### 3. Job Processors

**app/jobs/vision_batch.py** - Image Processing
- Batch process images via Gemini Flash vision model
- Extracts: subject, category, attributes, caption, confidence
- Validates output with Pydantic schemas
- Auto-flags low-confidence extractions

**app/jobs/embedding_batch.py** - Vector Generation
- Generates embeddings for image captions and posts
- Uses Gemini Text Embedding model
- Stores 768-dimensional vectors in pgvector

#### 4. API Routes

**GET /images** - List all images with pagination
**POST /images/batch-process** - Batch process image uploads
**GET /images/{id}** - Get specific image details

**POST /posts** - Create new post with embedding
**GET /posts** - List all posts
**GET /posts/{id}** - Get specific post

**GET /posts/{post_id}/images** - Get top image suggestions for post
- Returns matches that pass guard checks
- Ranked by cosine similarity
- Creates Suggestion records

**POST /posts/suggestions/{id}/approve** - Approve a suggestion
**POST /posts/suggestions/{id}/reject** - Reject a suggestion with reason

**GET /eval/precision** - Calculate top-1 precision on eval set
**GET /cost-log** - View all API cost logs
**GET /cost-log/summary** - Cost breakdown by type

**GET /health** - Service health check

## Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 13+ with pgvector extension
- Google Gemini API key

### Installation

1. Clone repository:
```bash
git clone <repo-url>
cd capstone-image-relevance
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup PostgreSQL:
```bash
# Create database
createdb flyrank

# Enable pgvector extension
psql flyrank -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

5. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Gemini API key and database URL
```

6. Run application:
```bash
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8001`
Interactive docs at `http://localhost:8001/docs`

## Workflow

### Image Processing
1. Upload images via `/images/batch-process`
2. Gemini Flash analyzes each image
3. Results validated and stored with embeddings
4. Low-confidence images auto-flagged

### Post Matching
1. Create post via `POST /posts`
2. Post text embedded automatically
3. Query `/posts/{post_id}/images` to find matches
4. System returns top suggestions passing guard checks
5. User approves/rejects suggestions

### Cost Tracking
- Every Gemini call logged with associated cost
- View detailed logs at `/cost-log`
- Summary breakdown at `/cost-log/summary`

### Evaluation
- Register ground truth in eval_set table
- Get precision metrics at `/eval/precision`
- Measures top-1 accuracy on test set

## Database Schema

### Images Table
```
id (PK) | filename (UNIQUE) | subject | category | attributes (JSON) | 
caption | confidence | flagged | embedding (Vector 768) | created_at
```

### Posts Table
```
id (PK) | title | content | embedding (Vector 768) | created_at
```

### Suggestions Table
```
id (PK) | post_id (FK) | image_id (FK) | similarity_score | 
guard_decision | guard_reason | status | approved_at | rejected_at | created_at
```

### CostLog Table
```
id (PK) | call_id (UNIQUE) | call_type | model | image_id (FK) | 
post_id (FK) | cost_usd | status | timestamp
```

### EvalSet Table
```
id (PK) | post_id (UNIQUE, FK) | correct_image_id (FK) | created_at
```

## Guard Logic

The mismatch guard prevents suggesting low-quality matches:

1. **Image Confidence Check**: Rejects if image extraction confidence < 0.85
2. **Similarity Check**: Rejects if embedding similarity < 0.75
3. **Combined Decision**: Match approved only if all checks pass

Failed matches return reasons explaining rejection.


## Results

**Top-1 precision: 6/7 = 85.7%** — measured with real Gemini-generated embeddings.

**Guard verification (wolf-on-fox rejection test):**

| Pair | Similarity | Decision |
|---|---|---|
| Wolf post → Fox image | 0.549 | ❌ REJECTED (below 0.75 threshold) |
| Fox post → Fox image | 0.722 | ✅ ACCEPTED |

One near-miss: the "Roses" post's top suggestion was a generic flower image rather than the ground-truth rose photo — an explainable confusion between botanically similar subjects, not a system failure.

### Known Limitations
- Small evaluation set (n=12) — one misclassification has an outsized effect on the precision percentage
- Free-tier API rate limits required delays between embedding calls during batch processing
- Closely related subjects (rose vs. flower, wolf vs. fox) can score similarly under general-purpose embeddings

## Cost Estimation

Approximate costs per operation (as of 2024):
- Vision analysis (Gemini Flash): $0.001 per image
- Text embedding: $0.00002 per text

Track actual usage at `/cost-log/summary`

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
SQLAlchemy handles schema creation automatically on startup.

### Adding New Routes
1. Create module in `app/routes/`
2. Define endpoints with FastAPI router
3. Import and include in `app/main.py`

## Troubleshooting

**No embeddings generated**: Check Gemini API key and quota
**Guard rejecting all matches**: Verify confidence/similarity thresholds in guard.py
**Database connection failed**: Check DATABASE_URL in .env and PostgreSQL running
**pgvector not found**: Run `CREATE EXTENSION IF NOT EXISTS vector;` in PostgreSQL

## License

Proprietary - FlyRank Capstone Project