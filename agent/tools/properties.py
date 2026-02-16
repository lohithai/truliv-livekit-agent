import httpx
from livekit.agents import function_tool, RunContext

from config import TRULIV_API_BASE_URL, TRULIV_API_KEY


@function_tool()
async def get_properties(ctx: RunContext, city: str, area: str = "") -> str:
    """Get the list of available Truliv PG properties in a given city and optionally a specific area.

    Args:
        city: The city to search in (e.g. "Chennai" or "Bangalore")
        area: Optional specific area or neighborhood (e.g. "Koramangala", "OMR", "HSR Layout")
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{TRULIV_API_BASE_URL}/properties",
                params={"city": city, "area": area},
                headers={"Authorization": f"Bearer {TRULIV_API_KEY}"},
            )
            response.raise_for_status()
            data = response.json()

        if not data:
            return f"No properties found in {city}" + (f", {area}" if area else "") + ". Would you like to check another area?"

        results = []
        for prop in data:
            name = prop.get("name", "Unknown")
            location = prop.get("area", "")
            price = prop.get("starting_price", "N/A")
            prop_id = prop.get("id", "")
            results.append(f"{name} in {location}, starting at Rs {price} per month (ID: {prop_id})")

        return f"Found {len(results)} properties: " + "; ".join(results)
    except httpx.HTTPError as e:
        return f"Sorry, I'm having trouble looking up properties right now. Please try again shortly."
