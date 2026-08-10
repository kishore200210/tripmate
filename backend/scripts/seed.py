"""
scripts/seed.py

Database seeder for TripMate development environment.

Purpose:
    - Populates the database with realistic sample Destinations and Documents.
    - Designed to be idempotent: running it multiple times will NOT create duplicates.
    - Provides enough data for the AI/RAG system to demo against.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed.py

Technologies:
    - SQLAlchemy AsyncSession
    - asyncio (async entry point)
"""

import asyncio
import sys
import os

# Allow imports from the backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
import app.db.model_registry  # noqa: F401
from app.modules.users.models import User
from app.modules.destinations.models import Destination, Document


# ── Seed Data ─────────────────────────────────────────────

DESTINATIONS = [
    {
        "name": "Bali",
        "country": "Indonesia",
        "description": (
            "A tropical island paradise known for its lush rice terraces, "
            "ancient temples, and world-class surf breaks. Perfect for couples, "
            "solo travelers, and spiritual seekers."
        ),
        "tags": ["beach", "culture", "spiritual", "adventure", "budget-friendly"],
        "image_url": "https://images.unsplash.com/photo-1537996194471-e657df975ab4",
        "avg_budget": 80.0,
    },
    {
        "name": "Paris",
        "country": "France",
        "description": (
            "The City of Light — renowned for the Eiffel Tower, world-class cuisine, "
            "fashion, art museums, and romantic ambiance along the Seine River."
        ),
        "tags": ["romance", "culture", "food", "art", "luxury"],
        "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34",
        "avg_budget": 200.0,
    },
    {
        "name": "Tokyo",
        "country": "Japan",
        "description": (
            "A dazzling blend of ultramodern and traditional — neon-lit skyscrapers "
            "stand next to historic temples. Famous for its food scene, cherry blossoms, "
            "and impeccable public transport."
        ),
        "tags": ["culture", "food", "technology", "family", "anime"],
        "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf",
        "avg_budget": 150.0,
    },
    {
        "name": "Cape Town",
        "country": "South Africa",
        "description": (
            "A vibrant city nestled between mountains and ocean. Table Mountain, "
            "Boulders Beach penguins, the Cape Winelands, and the V&A Waterfront "
            "make it one of Africa's most spectacular destinations."
        ),
        "tags": ["adventure", "nature", "wildlife", "beach", "wine"],
        "image_url": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99",
        "avg_budget": 120.0,
    },
    {
        "name": "New York City",
        "country": "United States",
        "description": (
            "The city that never sleeps. Times Square, Central Park, the Statue of Liberty, "
            "Broadway shows, and an unparalleled dining scene across five distinct boroughs."
        ),
        "tags": ["urban", "culture", "food", "entertainment", "shopping"],
        "image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9",
        "avg_budget": 250.0,
    },
]

DOCUMENTS = [
    {
        "destination_name": "Bali",
        "title": "Bali Travel Guide — Best Time to Visit",
        "content": (
            "The best time to visit Bali is during the dry season, from April to October. "
            "July and August are the most popular months, with clear skies perfect for "
            "beach activities, hiking Mount Batur, and temple hopping. "
            "The wet season runs from November to March, bringing heavy afternoon rains "
            "but also lush green landscapes and fewer tourists. "
            "Ubud is best visited year-round for yoga retreats and cultural experiences. "
            "Seminyak and Kuta are popular beach areas, while Nusa Penida offers dramatic cliffs."
        ),
    },
    {
        "destination_name": "Bali",
        "title": "Bali Travel Guide — Currency and Budget",
        "content": (
            "Bali uses the Indonesian Rupiah (IDR). As of 2025, 1 USD is approximately "
            "16,000 IDR. Bali is very budget-friendly — a street meal (Nasi Goreng) costs "
            "around 30,000–50,000 IDR (~$2–$3). Mid-range restaurants cost $10–$20 per person. "
            "Accommodation ranges from $10/night guesthouses in Ubud to $500/night luxury villas. "
            "The average daily budget is $50–$80 for a comfortable mid-range experience. "
            "ATMs are widely available in tourist areas. Inform your bank before travel."
        ),
    },
    {
        "destination_name": "Tokyo",
        "title": "Tokyo Travel Guide — Getting Around",
        "content": (
            "Tokyo has one of the world's most efficient public transport networks. "
            "The JR Pass is ideal for tourists visiting multiple cities. "
            "The Tokyo Metro and Toei Subway cover the entire city. "
            "Buy a Suica or Pasmo IC card for seamless travel on trains, buses, and even "
            "convenience store purchases. Taxis are expensive — typically $20–$40 for short trips. "
            "The airport is connected by the Narita Express (NEX) train or the Limousine Bus. "
            "Cycling is popular in residential areas and there are many bike-share programs."
        ),
    },
    {
        "destination_name": "Paris",
        "title": "Paris Travel Guide — Must-See Attractions",
        "content": (
            "Paris is packed with iconic sights. The Eiffel Tower is best visited at night "
            "when it sparkles with lights — book tickets online in advance to skip queues. "
            "The Louvre Museum houses the Mona Lisa and thousands of other masterpieces — "
            "allow at least 3 hours. The Musee d'Orsay showcases Impressionist art. "
            "Notre-Dame Cathedral is under restoration but the exterior is worth seeing. "
            "Montmartre's Sacre-Coeur offers panoramic city views. "
            "Day trips: Versailles Palace (45 min by RER C train) and Monet's Gardens in Giverny."
        ),
    },
]


async def seed_database() -> None:
    """Idempotently seed the database with sample destinations and documents."""
    print("🌱 Starting database seeding...")

    async with AsyncSessionLocal() as session:
        # ── Seed Destinations ──────────────────────────────
        dest_map: dict[str, Destination] = {}
        for dest_data in DESTINATIONS:
            # Check if destination already exists (idempotent)
            result = await session.execute(
                select(Destination).where(Destination.name == dest_data["name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"   ⏭  Destination '{dest_data['name']}' already exists. Skipping.")
                dest_map[dest_data["name"]] = existing
            else:
                destination = Destination(**dest_data)
                session.add(destination)
                await session.flush()  # Get the ID before commit
                dest_map[dest_data["name"]] = destination
                print(f"   ✅ Created destination: {dest_data['name']}")

        # ── Seed Documents ─────────────────────────────────
        for doc_data in DOCUMENTS:
            dest_name = doc_data.pop("destination_name")
            destination = dest_map.get(dest_name)
            if not destination:
                print(f"   ⚠️  Destination '{dest_name}' not found. Skipping document.")
                continue

            result = await session.execute(
                select(Document).where(Document.title == doc_data["title"])
            )
            existing_doc = result.scalar_one_or_none()

            if existing_doc:
                print(f"   ⏭  Document '{doc_data['title']}' already exists. Skipping.")
            else:
                document = Document(**doc_data, destination_id=destination.id)
                session.add(document)
                print(f"   ✅ Created document: {doc_data['title']}")

        await session.commit()

    print("\n🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
