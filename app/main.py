"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.routes import images, posts, suggestions, eval_routes, cost_routes

app = FastAPI(
    title="FlyRank AI Image Understanding",
    description="AI Image Understanding & Content Matching Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()
    print("Application started, database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "FlyRank"}


app.include_router(images.router)
app.include_router(posts.router)
app.include_router(suggestions.router)
app.include_router(eval_routes.router)
app.include_router(cost_routes.router)
