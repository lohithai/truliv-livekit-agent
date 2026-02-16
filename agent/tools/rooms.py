import httpx
from livekit.agents import function_tool, RunContext

from config import TRULIV_API_BASE_URL, TRULIV_API_KEY


@function_tool()
async def get_room_availability(ctx: RunContext, property_id: str) -> str:
    """Check room availability for a specific Truliv property.

    Args:
        property_id: The property ID to check room availability for
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{TRULIV_API_BASE_URL}/properties/{property_id}/rooms",
                headers={"Authorization": f"Bearer {TRULIV_API_KEY}"},
            )
            response.raise_for_status()
            data = response.json()

        if not data:
            return f"No rooms are currently available at this property. Would you like to check another property?"

        results = []
        for room in data:
            room_type = room.get("type", "Unknown")
            available = room.get("available_count", 0)
            price = room.get("price", "N/A")
            results.append(f"{room_type}: {available} available at Rs {price}/month")

        return f"Room availability: " + "; ".join(results)
    except httpx.HTTPError:
        return "Sorry, I'm having trouble checking room availability right now. Please try again shortly."
