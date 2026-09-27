import os
from dotenv import load_dotenv
import google.generativeai as genai
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("=== Testing with output_dimensionality=768 ===")
try:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content="test fox in snow",
        output_dimensionality=768,
    )
    print("Success! Vector length:", len(result["embedding"]))
except Exception as e:
    print("Failed:", type(e).__name__, "-", e)