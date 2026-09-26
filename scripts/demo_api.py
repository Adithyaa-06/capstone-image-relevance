"""
Demo script to test API endpoints.

Usage:
    python scripts/demo_api.py
"""

import requests
import json

API_BASE = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("\n🏥 Testing /health endpoint")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_list_images():
    """Test listing images."""
    print("\n🖼️  Testing GET /images")
    try:
        response = requests.get(f"{API_BASE}/images")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Images found: {len(data)}")
        if data:
            print(f"   First image: {data[0]['filename']}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_list_posts():
    """Test listing posts."""
    print("\n📝 Testing GET /posts")
    try:
        response = requests.get(f"{API_BASE}/posts")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Posts found: {len(data)}")
        if data:
            print(f"   First post: {data[0]['title']}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_cost_summary():
    """Test cost summary endpoint."""
    print("\n💰 Testing GET /cost-log/summary")
    try:
        response = requests.get(f"{API_BASE}/cost-log/summary")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total cost: ${data['total_cost']:.4f}")
        print(f"   Total calls: {data['total_calls']}")
        print(f"   By type: {json.dumps(data['by_type'], indent=4)}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_get_suggestions(post_id: int = 1):
    """Test getting suggestions for a post."""
    print(f"\n🎯 Testing GET /posts/{post_id}/images")
    try:
        response = requests.get(f"{API_BASE}/posts/{post_id}/images")
        data = response.json()
        print(f"   Status: {response.status_code}")
        if isinstance(data, list):
            print(f"   Suggestions found: {len(data)}")
            if data:
                print(f"   Top suggestion: {data[0]['filename']} (score: {data[0]['similarity_score']:.3f})")
        elif isinstance(data, dict) and "message" in data:
            print(f"   Message: {data['message']}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_precision():
    """Test precision metric."""
    print("\n📊 Testing GET /eval/precision")
    try:
        response = requests.get(f"{API_BASE}/eval/precision")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total posts: {data['total_posts']}")
        print(f"   Correct (top-1): {data['correct_top1']}")
        print(f"   Precision: {data['precision']:.3f}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def main():
    print("🧪 FlyRank API Demo")
    print("=" * 50)
    print("\n⚠️  Make sure the server is running:")
    print("   uvicorn app.main:app --reload")

    test_health()
    test_list_images()
    test_list_posts()
    test_cost_summary()
    test_get_suggestions()
    test_precision()

    print("\n" + "=" * 50)
    print("✅ Demo complete!")
    print("\nView interactive docs at:")
    print(f"   {API_BASE}/docs")


if __name__ == "__main__":
    main()
