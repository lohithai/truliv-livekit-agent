import httpx
from livekit.agents import function_tool, RunContext

from config import GOOGLE_MAPS_API_KEY


@function_tool()
async def get_location(ctx: RunContext, address: str) -> str:
    """Get the full address and location details for a place using Google Geolocation API.

    Args:
        address: The property name, address, or area to look up (e.g. "Truliv HSR Layout Bangalore")
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": GOOGLE_MAPS_API_KEY},
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return f"I couldn't find location details for '{address}'. Could you provide a more specific address?"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", "")
        location = result.get("geometry", {}).get("location", {})
        lat = location.get("lat", "")
        lng = location.get("lng", "")

        return f"The address is: {formatted_address}. You can find it on Google Maps by searching for these coordinates: {lat}, {lng}."
    except httpx.HTTPError:
        return "Sorry, I'm having trouble looking up the location right now. Please try again shortly."
