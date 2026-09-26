# FlyRank - Requirements Evidence

## Requirement Traceability

### Database Models ✅

**Requirement**: Image (filename, subject, category, attributes, caption, confidence, embedding, flagged)
- **File**: app/models/database.py:9-25
- **Evidence**: Image class with all required columns

**Requirement**: Post (title, content, embedding)
- **File**: app/models/database.py:27-37
- **Evidence**: Post class with columns and relationship to Suggestions

**Requirement**: Suggestion (post_id, image_id, similarity_score, guard_decision, guard_reason, status)
- **File**: app/models/database.py:39-58
- **Evidence**: Suggestion class with all required fields plus approval tracking

**Requirement**: CostLog (call_id, call_type, model, cost_usd, timestamp)
- **File**: app/models/database.py:60-74
- **Evidence**: CostLog class with complete cost tracking fields

**Requirement**: EvalSet (post_id, correct_image_id)
- **File**: app/models/database.py:76-82
- **Evidence**: EvalSet class for ground truth evaluation

### Core Modules ✅

**Requirement**: app/core/guard.py - Mismatch guard (reject if: confidence < 0.85 OR similarity < 0.75 OR semantic mismatch)
- **File**: app/core/guard.py
- **Evidence**: 
  - Line 10-32: evaluate_match() function with three rejection criteria
  - Confidence threshold: line 19-23
  - Similarity threshold: line 25-29
  - Returns GuardDecision with approval status

**Requirement**: app/core/cost_tracker.py - Log every Gemini call
- **File**: app/core/cost_tracker.py
- **Evidence**: 
  - line 10-44: log_gemini_call() records call_id, call_type, model, cost_usd
  - line 46-48: get_total_cost() aggregation
  - line 51-57: get_costs_by_type() breakdown

**Requirement**: app/core/database.py - PostgreSQL setup with pgvector
- **File**: app/core/database.py
- **Evidence**: 
  - line 1-5: SQLAlchemy engine with DATABASE_URL
  - line 10: SessionLocal for connection pooling
  - line 13-15: init_db() creates all tables with Vector columns

### Job Processors ✅

**Requirement**: app/jobs/vision_batch.py - Batch process images via Gemini Flash
- **File**: app/jobs/vision_batch.py
- **Evidence**:
  - line 20-48: process_image_file() with Gemini vision model
  - line 8-14: model initialization
  - line 50-73: save_image_record() with auto-flagging

**Requirement**: Validate with Pydantic
- **File**: app/jobs/vision_batch.py:26
- **Evidence**: ImageTag(**result) validates schema

**Requirement**: Log costs
- **File**: app/jobs/vision_batch.py:135-141
- **Evidence**: log_gemini_call() for vision analysis cost

**Requirement**: app/jobs/embedding_batch.py - Embed image captions + posts via Gemini embeddings
- **File**: app/jobs/embedding_batch.py
- **Evidence**:
  - line 18-31: generate_embedding() using text-embedding-004
  - line 34-64: embed_image_captions() batch process
  - line 67-96: embed_posts() with combined title+content

### API Routes ✅

**Requirement**: POST /images/batch-process
- **File**: app/routes/images.py:25-59
- **Evidence**: Accepts file uploads, processes with vision model

**Requirement**: GET /images/{id}
- **File**: app/routes/images.py:62-81
- **Evidence**: Retrieves single image record

**Requirement**: POST /posts
- **File**: app/routes/posts.py:20-45
- **Evidence**: Creates post with auto-generated embedding

**Requirement**: GET /posts/{id}
- **File**: app/routes/posts.py:48-61
- **Evidence**: Retrieves post by ID

**Requirement**: GET /posts/{post_id}/images
- **File**: app/routes/suggestions.py:30-99
- **Evidence**: Returns suggestions passing guard checks

**Requirement**: POST /suggestions/{id}/approve
- **File**: app/routes/suggestions.py:102-118
- **Evidence**: Updates suggestion status to approved

**Requirement**: POST /suggestions/{id}/reject
- **File**: app/routes/suggestions.py:121-138
- **Evidence**: Updates suggestion status to rejected with reason

**Requirement**: GET /eval/precision
- **File**: app/routes/eval_routes.py:18-64
- **Evidence**: Calculates top-1 precision on eval set

**Requirement**: GET /cost-log
- **File**: app/routes/cost_routes.py:17-40
- **Evidence**: Lists all cost logs with optional filtering

### Configuration Files ✅

**Requirement**: requirements.txt
- **File**: requirements.txt
- **Evidence**: Lists all dependencies including FastAPI, SQLAlchemy, pgvector, google-generativeai

**Requirement**: capstone.yaml (manifest with endpoints)
- **File**: capstone.yaml
- **Evidence**: Complete endpoint list with parameters and descriptions

**Requirement**: README.md (architecture, setup, requirements)
- **File**: README.md
- **Evidence**: Full documentation with setup instructions and workflow

**Requirement**: .env.example (all env vars needed)
- **File**: .env.example
- **Evidence**: GEMINI_API_KEY and DATABASE_URL templates

**Requirement**: BUILDLOG.md (AI usage tracker)
- **File**: BUILDLOG.md
- **Evidence**: Cost estimation and feature tracking

**Requirement**: EVIDENCE.md (requirements proof)
- **File**: EVIDENCE.md
- **Evidence**: This file - complete traceability matrix

### Main Application ✅

**Requirement**: app/main.py - FastAPI app with all routers, startup init
- **File**: app/main.py
- **Evidence**:
  - line 10-18: FastAPI setup with CORS
  - line 21-24: Startup initialization
  - line 35-39: All routers included

### Testing ✅

**Requirement**: tests/test_guard.py - Test guard logic (pytest)
- **File**: tests/test_guard.py
- **Evidence**: Test cases for guard thresholds

**Requirement**: tests/test_schemas.py - Test Pydantic validation
- **File**: tests/test_schemas.py
- **Evidence**: Schema validation tests

### Stack Validation ✅

**Requirement**: Use Gemini Flash for vision
- **Evidence**: app/jobs/vision_batch.py:14 uses "gemini-2.0-flash"

**Requirement**: Use Gemini embeddings for vectors
- **Evidence**: app/jobs/embedding_batch.py:22 uses "text-embedding-004"

**Requirement**: FastAPI + PostgreSQL + pgvector
- **Evidence**:
  - FastAPI: app/main.py
  - PostgreSQL: app/core/database.py
  - pgvector: app/models/database.py imports Vector

## Summary

All 30+ requirements documented with specific file locations and line numbers.
Complete implementation includes:
- 5 database models
- 3 core modules
- 2 job processors
- 5 route modules
- 1 main application
- 6 configuration files
- 2 test modules

**Status**: COMPLETE ✅
