#!/usr/bin/env python
"""List all images with their metadata."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.database import Image

db = SessionLocal()
try:
    images = db.query(Image).all()
    print("All Images:")
    print("=" * 80)
    for img in images:
        print(f"ID={img.id:2d} | {img.filename:20s} | {img.subject:15s} | {img.category:10s} | confidence={img.confidence:.3f}")
finally:
    db.close()
