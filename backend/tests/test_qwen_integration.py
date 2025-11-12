"""
Test Qwen VL integration with MultiProviderVLMClient

Purpose: Verify that Qwen VL adapter works correctly through the main VLM client

Author: AI Python Architect
Date: 2025-11-13
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient
from backend.infrastructure.llm.prompts.response_schema import Q02Response

print("=" * 80)
print("Qwen VL Integration Test")
print("=" * 80)

# 1. Initialize client with only Qwen provider
print("\n[STEP 1] Initializing MultiProviderVLMClient with Qwen only...")
try:
    client = MultiProviderVLMClient(
        providers=["qwen"],  # Only use Qwen
        enable_cache=False   # Disable cache for testing
    )
    print("[OK] Client initialized successfully")
except Exception as e:
    print(f"[FAIL] Failed to initialize client: {e}")
    sys.exit(1)

# 2. Load test image
print("\n[STEP 2] Loading test image...")
test_image_path = project_root / "venv" / "Lib" / "site-packages" / "streamlit" / "static" / "favicon.png"
if not test_image_path.exists():
    print(f"[FAIL] Test image not found: {test_image_path}")
    sys.exit(1)

with open(test_image_path, 'rb') as f:
    test_image = f.read()

print(f"[OK] Test image loaded: {len(test_image)} bytes")

# 3. Query VLM
print("\n[STEP 3] Querying Qwen VL through MultiProviderVLMClient...")
try:
    response = client.query_structured(
        prompt='Identify the genus of this flower: Rosa, Prunus, Tulipa, Dianthus, Paeonia, or unknown. Please respond ONLY with a JSON object in this exact format: {"choice": "value", "confidence": 0.0, "reasoning": "brief explanation"}',
        response_model=Q02Response,
        image_bytes=test_image
    )

    print("[SUCCESS] Qwen VL query completed!")
    print(f"   Response type: {type(response).__name__}")
    print(f"   Genus: {response.choice}")
    print(f"   Confidence: {response.confidence}")
    print(f"   Reasoning: {response.reasoning}")

except Exception as e:
    print(f"[FAIL] Query failed: {type(e).__name__}: {str(e)}")
    sys.exit(1)

print("\n" + "=" * 80)
print("Test completed successfully!")
print("=" * 80)
