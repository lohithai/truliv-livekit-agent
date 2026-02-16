import httpx
from livekit.agents import function_tool, RunContext

from config import TRULIV_API_BASE_URL, TRULIV_API_KEY


@function_tool()
async def get_bed_availability(ctx: RunContext, property_id: str) -> str:
    """Check bed availability for a specific Truliv property.

    Args:
        property_id: The property ID to check bed availability for
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{TRULIV_API_BASE_URL}/properties/{property_id}/beds",
                headers={"Authorization": f"Bearer {TRULIV_API_KEY}"},
            )
            response.raise_for_status()
            data = response.json()

        if not data:
            return f"No beds are currently available at this property. Would you like to check another property?"

        results = []
        for bed in data:
            bed_type = bed.get("type", "Unknown")
            available = bed.get("available_count", 0)
            price = bed.get("price", "N/A")
            results.append(f"{bed_type}: {available} available at Rs {price}/month")

        return f"Bed availability: " + "; ".join(results)
    except httpx.HTTPError:
        return "Sorry, I'm having trouble checking bed availability right now. Please try again shortly."
