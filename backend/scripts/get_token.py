import asyncio
import app.db.model_registry
from app.db.session import AsyncSessionLocal
from app.modules.trips.models import Trip
from app.modules.users.models import User
from app.core.security import create_access_token

async def main():
    async with AsyncSessionLocal() as session:
        trip = await session.get(Trip, "9b64e398-bba1-491d-a78d-364ebc4a05e4")
        if trip:
            user = await session.get(User, trip.user_id)
            token = create_access_token(user_id=trip.user_id, role=user.role.value if user else "user")
            print(token)
        else:
            print("Trip not found")

asyncio.run(main())
