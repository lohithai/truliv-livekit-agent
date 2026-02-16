import os
from dotenv import load_dotenv

load_dotenv(".env.local")

# LiveKit
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")

# AI Services
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")

# Truliv APIs
TRULIV_API_BASE_URL = os.getenv("TRULIV_API_BASE_URL", "")
TRULIV_API_KEY = os.getenv("TRULIV_API_KEY", "")

# Google Maps
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# SIP
SIP_TRUNK_OUTBOUND_ID = os.getenv("SIP_TRUNK_OUTBOUND_ID", "")
HUMAN_TRANSFER_NUMBER = os.getenv("HUMAN_TRANSFER_NUMBER", "")

# Agent
AGENT_NAME = "truliv-telephony-agent"
