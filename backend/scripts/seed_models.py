#!/usr/bin/env python3
"""
Seed script to populate the AI models collection with initial model configurations.

This script adds popular models from OpenAI, Google (Gemini), and Cerebras.

IMPORTANT: Run this script from the correct directory!

1. If running locally:
   cd /path/to/your/gaia/backend
   python scripts/seed_models.py

2. If running inside Docker container:
   cd /app
   python scripts/seed_models.py

3. Alternative Docker approach (set PYTHONPATH):
   PYTHONPATH=/app python scripts/seed_models.py

4. Run as module (from app directory):
   python -m scripts.seed_models

"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the backend directory to Python path so we can import from app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import app modules after path setup  # noqa: E402
from app.db.mongodb.collections import ai_models_collection  # noqa: E402
from app.models.models_models import ModelProvider, PlanType  # noqa: E402


async def seed_models():
    """Seed the AI models collection with initial data."""

    # Check if models already exist
    existing_count = await ai_models_collection.count_documents({})
    if existing_count > 0:
        print(
            f"Models collection already has {existing_count} documents. Skipping seed."
        )
        return

    models_to_seed = [
        # OpenAI Models
        {
            "model_id": "gpt-4o",
            "name": "GPT-4o",
            "model_provider": ModelProvider.OPENAI.value,
            "inference_provider": ModelProvider.OPENAI.value,
            "provider_model_name": "gpt-4o",
            "description": "OpenAI's most capable model, great for complex reasoning tasks",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/e/ef/ChatGPT-Logo.svg",
            "max_tokens": 48_000,
            "supports_streaming": True,
            "supports_function_calling": True,
            "available_in_plans": [
                PlanType.PRO.value,
            ],
            "lowest_tier": PlanType.PRO.value,
            "is_active": True,
            "is_default": False,
            "pricing_per_1k_input_tokens": 0.0025,
            "pricing_per_1k_output_tokens": 0.01,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "model_id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "model_provider": ModelProvider.OPENAI.value,
            "inference_provider": ModelProvider.OPENAI.value,
            "provider_model_name": "gpt-4o-mini",
            "description": "OpenAI's efficient model, fast and cost-effective for most tasks",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/e/ef/ChatGPT-Logo.svg",
            "max_tokens": 120_000,
            "supports_streaming": True,
            "supports_function_calling": True,
            "available_in_plans": [
                PlanType.FREE.value,
                PlanType.PRO.value,
            ],
            "lowest_tier": PlanType.FREE.value,
            "is_active": True,
            "is_default": True,  # Set as default for free users
            "pricing_per_1k_input_tokens": 0.00015,
            "pricing_per_1k_output_tokens": 0.0006,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        # Google Gemini Models
        {
            "model_id": "gemini-1.5-flash",
            "name": "Gemini 1.5 Flash",
            "model_provider": ModelProvider.GEMINI.value,
            "inference_provider": ModelProvider.GEMINI.value,
            "provider_model_name": "gemini-1.5-flash",
            "description": "Google's fast and efficient model for quick responses",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Google_Gemini_icon_2025.svg/1024px-Google_Gemini_icon_2025.svg.png",
            "max_tokens": 8192,
            "supports_streaming": True,
            "supports_function_calling": True,
            "available_in_plans": [
                PlanType.FREE.value,
                PlanType.PRO.value,
            ],
            "lowest_tier": PlanType.FREE.value,
            "is_active": True,
            "is_default": False,
            "pricing_per_1k_input_tokens": 0.000075,
            "pricing_per_1k_output_tokens": 0.0003,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "model_id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "model_provider": ModelProvider.GEMINI.value,
            "inference_provider": ModelProvider.GEMINI.value,
            "provider_model_name": "gemini-1.5-pro",
            "description": "Google's most capable model with advanced reasoning capabilities",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Google_Gemini_icon_2025.svg/1024px-Google_Gemini_icon_2025.svg.png",
            "max_tokens": 8192,
            "supports_streaming": True,
            "supports_function_calling": True,
            "available_in_plans": [
                PlanType.PRO.value,
            ],
            "lowest_tier": PlanType.PRO.value,
            "is_active": True,
            "is_default": False,
            "pricing_per_1k_input_tokens": 0.00125,
            "pricing_per_1k_output_tokens": 0.005,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        # Cerebras Models (using GPT logo since it's running GPT model)
        {
            "model_id": "gpt-oss-120b",
            "name": "GPT OSS 120B",
            "model_provider": ModelProvider.OPENAI.value,
            "inference_provider": ModelProvider.CEREBRAS.value,
            "provider_model_name": "gpt-oss-120b",
            "description": "Cerebras' open-source model, high performance with fast inference",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/e/ef/ChatGPT-Logo.svg",
            "max_tokens": 120_000,
            "supports_streaming": True,
            "supports_function_calling": True,
            "available_in_plans": [
                PlanType.FREE.value,
                PlanType.PRO.value,
            ],
            "lowest_tier": PlanType.FREE.value,
            "is_active": True,
            "is_default": False,
            "pricing_per_1k_input_tokens": 0.0001,
            "pricing_per_1k_output_tokens": 0.0001,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]

    try:
        # Insert all models
        result = await ai_models_collection.insert_many(models_to_seed)
        print(f"Successfully seeded {len(result.inserted_ids)} models:")

        for model in models_to_seed:
            print(f"  - {model['name']} ({model['model_id']}) - {model['provider']}")

        print("\nSeed completed successfully!")

    except Exception as e:
        print(f"Error seeding models: {e}")
        raise


async def main():
    """Main function to run the seed script."""
    print("Starting AI models seed script...")
    await seed_models()


if __name__ == "__main__":
    asyncio.run(main())
