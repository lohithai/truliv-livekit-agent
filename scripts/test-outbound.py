"""Test outbound call via Truliv voice agent.

Usage: python scripts/test-outbound.py +919876543210
"""
import asyncio
import json
import os
import random
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test-outbound.py <phone_number>")
        print("Example: python scripts/test-outbound.py +919876543210")
        sys.exit(1)

    phone_number = sys.argv[1]
    room_name = f"outbound-{''.join(str(random.randint(0, 9)) for _ in range(10))}"

    lkapi = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    print(f"Dispatching outbound call to {phone_number} in room {room_name}...")

    await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="truliv-telephony-agent",
            room=room_name,
            metadata=json.dumps({"phone_number": phone_number}),
        )
    )

    print(f"Call dispatched! Room: {room_name}")
    await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(main())
