"""
Initialize the database from scratch.
Creates all tables and sets up pgvector extension.

Usage:
    python scripts/init_db.py
"""

from app.core.database import init_db


def main():
    print("🗄️  FlyRank Database Initialization")
    print("=" * 50)

    try:
        print("\n📋 Creating database tables...")
        init_db()
        print("✅ Database initialized successfully!")
        print("\n   Tables created:")
        print("   - images")
        print("   - posts")
        print("   - suggestions")
        print("   - cost_logs")
        print("   - eval_set")

    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        print("\n   Make sure PostgreSQL is running and pgvector is installed:")
        print("   createdb flyrank")
        print("   psql flyrank -c 'CREATE EXTENSION IF NOT EXISTS vector;'")


if __name__ == "__main__":
    main()
