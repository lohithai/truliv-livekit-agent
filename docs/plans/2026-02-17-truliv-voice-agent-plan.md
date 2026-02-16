# Truliv Voice AI Agent - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and deploy a self-hosted LiveKit voice AI agent on AWS EC2 for Truliv (co-living/PG provider) that handles inbound/outbound phone calls via SIP with Deepgram STT, Google Gemini 2.5 Flash LLM, and Cartesia TTS.

**Architecture:** Single AWS EC2 instance (c5.2xlarge, Mumbai region) running LiveKit Server, LiveKit SIP, Redis, Caddy, and the Python voice agent via Docker Compose. Phone calls arrive via custom SIP trunk, get bridged into LiveKit rooms, where the Python agent processes speech and responds using AI services.

**Tech Stack:** Python 3.10+, LiveKit Agents SDK 1.3, Docker Compose, Caddy, Redis, Deepgram, Google Gemini, Cartesia, AWS EC2 (Ubuntu 24.04)

**Design Doc:** `docs/plans/2026-02-17-truliv-voice-agent-design.md`

---

## Phase 1: Project Initialization & Local Setup

### Task 1: Initialize Git Repository and Project Structure

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `agent/`, `deploy/`, `scripts/` directories

**Step 1: Initialize git repo**

Run:
```bash
cd /Users/lohith/Desktop/Projects/livekitlatest
git init
```
Expected: `Initialized empty Git repository`

**Step 2: Create .gitignore**

Create `.gitignore`:
```
# Environment
.env
.env.local
*.env

# Python
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yaml
```

**Step 3: Create .env.example**

Create `.env.example`:
```bash
# LiveKit Server (generated during deployment)
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LIVEKIT_URL=wss://livekit.truliv.supercx.co

# AI Services
DEEPGRAM_API_KEY=
GOOGLE_API_KEY=
CARTESIA_API_KEY=

# Google Geolocation
GOOGLE_MAPS_API_KEY=

# Truliv APIs
TRULIV_API_BASE_URL=
TRULIV_API_KEY=

# SIP Configuration
SIP_TRUNK_OUTBOUND_ID=
HUMAN_TRANSFER_NUMBER=
```

**Step 4: Create directory structure**

Run:
```bash
mkdir -p agent/tools deploy/sip deploy/setup scripts
```

**Step 5: Commit**

```bash
git add .gitignore .env.example docs/
git commit -m "chore: initialize project with structure and design docs"
```

---

### Task 2: Set Up Python Project with Dependencies

**Files:**
- Create: `agent/pyproject.toml`

**Step 1: Install uv (Python package manager)**

Run:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Expected: uv installed successfully

**Step 2: Initialize Python project**

Run:
```bash
cd /Users/lohith/Desktop/Projects/livekitlatest/agent
uv init --name truliv-agent
```

**Step 3: Write pyproject.toml**

Replace `agent/pyproject.toml` with:
```toml
[project]
name = "truliv-agent"
version = "0.1.0"
description = "Truliv Voice AI Agent powered by LiveKit"
requires-python = ">=3.10,<3.14"
dependencies = [
    "livekit-agents[silero,turn-detector,google,deepgram,cartesia]~=1.3",
    "livekit-plugins-noise-cancellation~=0.2",
    "python-dotenv",
    "httpx",
]

[project.scripts]
agent = "main:main"
```

**Step 4: Install dependencies**

Run:
```bash
cd /Users/lohith/Desktop/Projects/livekitlatest/agent
uv sync
```
Expected: All packages installed without errors

**Step 5: Commit**

```bash
cd /Users/lohith/Desktop/Projects/livekitlatest
git add agent/pyproject.toml agent/uv.lock
git commit -m "chore: set up Python project with LiveKit agent dependencies"
```

---

## Phase 2: Build the Voice Agent (Python)

### Task 3: Create Agent Configuration and Prompts

**Files:**
- Create: `agent/config.py`
- Create: `agent/prompts.py`

**Step 1: Create config.py**

Create `agent/config.py`:
```python
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
```

**Step 2: Create prompts.py**

Create `agent/prompts.py`:
```python
TRULIV_SYSTEM_PROMPT = """You are Truliv Assistant, a friendly and helpful voice AI agent for Truliv, \
a co-living and PG (Paying Guest) accommodation provider operating in Chennai and Bangalore, India.

Your role:
- Help callers find available PG properties, rooms, and beds
- Provide location and address details for properties
- Answer common questions about Truliv's co-living spaces (pricing, amenities, rules, move-in process)
- Be warm, professional, and conversational

Key behaviors:
- Keep responses concise and natural for voice conversation (2-3 sentences max)
- When a caller asks about properties, use the get_properties tool to look up available options
- When they ask about room or bed availability, use the appropriate tool with the property ID
- When they ask about location or directions, use the get_location tool
- If you cannot help with something, offer to transfer them to a human agent
- Speak clearly and avoid complex formatting, punctuation, or symbols
- You support English, Hindi, Tamil, and Kannada - respond in the language the caller uses

About Truliv:
- Truliv offers fully-furnished co-living PG spaces for working professionals and students
- Properties are available in Chennai and Bangalore
- Amenities typically include WiFi, meals, housekeeping, laundry, and security
"""

INBOUND_GREETING = "Greet the caller warmly. Say: Hello, welcome to Truliv! I'm your AI assistant. I can help you find available PG accommodations in Chennai or Bangalore, check room availability, or answer any questions. How can I help you today?"

OUTBOUND_RENT_REMINDER = "You are calling a Truliv tenant to remind them about their upcoming rent payment. Be polite and brief. Start by confirming you're speaking with the right person."

OUTBOUND_FOLLOWUP = "You are following up on a property inquiry. Be friendly and ask if they have any remaining questions or would like to schedule a visit."
```

**Step 3: Commit**

```bash
git add agent/config.py agent/prompts.py
git commit -m "feat: add agent configuration and Truliv system prompts"
```

---

### Task 4: Create API Integration Tools

**Files:**
- Create: `agent/tools/__init__.py`
- Create: `agent/tools/properties.py`
- Create: `agent/tools/rooms.py`
- Create: `agent/tools/beds.py`
- Create: `agent/tools/geolocation.py`

**Step 1: Create tools/__init__.py**

Create `agent/tools/__init__.py`:
```python
from .properties import get_properties
from .rooms import get_room_availability
from .beds import get_bed_availability
from .geolocation import get_location

__all__ = [
    "get_properties",
    "get_room_availability",
    "get_bed_availability",
    "get_location",
]
```

**Step 2: Create properties.py**

Create `agent/tools/properties.py`:
```python
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
```

**Step 3: Create rooms.py**

Create `agent/tools/rooms.py`:
```python
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
```

**Step 4: Create beds.py**

Create `agent/tools/beds.py`:
```python
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
```

**Step 5: Create geolocation.py**

Create `agent/tools/geolocation.py`:
```python
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
```

**Step 6: Commit**

```bash
git add agent/tools/
git commit -m "feat: add Truliv API integration tools (properties, rooms, beds, geolocation)"
```

---

### Task 5: Create the Main Agent and Entry Point

**Files:**
- Create: `agent/assistant.py`
- Create: `agent/main.py`

**Step 1: Create assistant.py**

Create `agent/assistant.py`:
```python
import json

from livekit import agents, api, rtc
from livekit.agents import Agent, AgentSession, RunContext, function_tool, get_job_context

from config import HUMAN_TRANSFER_NUMBER
from prompts import TRULIV_SYSTEM_PROMPT
from tools import get_properties, get_room_availability, get_bed_availability, get_location


class TrulivAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=TRULIV_SYSTEM_PROMPT,
            tools=[
                get_properties,
                get_room_availability,
                get_bed_availability,
                get_location,
                self.transfer_to_human,
            ],
        )

    @function_tool()
    async def transfer_to_human(self, ctx: RunContext) -> str:
        """Transfer the call to a human support agent. Use this when the caller explicitly asks to speak to a person, or when you cannot resolve their issue."""
        await ctx.session.generate_reply(
            instructions="Tell the caller you're transferring them to a human agent and to please hold."
        )

        job_ctx = get_job_context()
        try:
            # Find the SIP participant to transfer
            participants = job_ctx.room.remote_participants
            sip_participant = None
            for p in participants.values():
                if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    sip_participant = p
                    break

            if sip_participant and HUMAN_TRANSFER_NUMBER:
                await job_ctx.api.sip.transfer_sip_participant(
                    api.TransferSIPParticipantRequest(
                        room_name=job_ctx.room.name,
                        participant_identity=sip_participant.identity,
                        transfer_to=f"tel:{HUMAN_TRANSFER_NUMBER}",
                    )
                )
                return "Call transferred successfully."
            else:
                return "I'm sorry, I couldn't transfer the call right now. Please call our support number directly."
        except Exception as e:
            print(f"Error transferring call: {e}")
            return "I'm sorry, I couldn't transfer the call right now. Please call our support number directly."
```

**Step 2: Create main.py**

Create `agent/main.py`:
```python
import json

from dotenv import load_dotenv

from livekit import agents, api, rtc
from livekit.agents import AgentServer, AgentSession, room_io
from livekit.plugins import cartesia, deepgram, google, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from assistant import TrulivAssistant
from config import AGENT_NAME, SIP_TRUNK_OUTBOUND_ID
from prompts import INBOUND_GREETING

load_dotenv(".env.local")

server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def truliv_agent(ctx: agents.JobContext):
    # Check if this is an outbound call by reading metadata
    phone_number = None
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
            phone_number = metadata.get("phone_number")
        except json.JSONDecodeError:
            pass

    # If outbound, place the SIP call
    if phone_number:
        sip_participant_identity = phone_number
        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=SIP_TRUNK_OUTBOUND_ID,
                    sip_call_to=phone_number,
                    participant_identity=sip_participant_identity,
                    wait_until_answered=True,
                )
            )
            print(f"Outbound call to {phone_number} answered successfully")
        except api.TwirpError as e:
            print(
                f"Error creating SIP participant: {e.message}, "
                f"SIP status: {e.metadata.get('sip_status_code')} "
                f"{e.metadata.get('sip_status')}"
            )
            ctx.shutdown()
            return

    # Create the agent session with STT-LLM-TTS pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=cartesia.TTS(model="sonic", language="en"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=TrulivAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # For inbound calls, greet the caller. For outbound, wait for the person to speak first.
    if phone_number is None:
        await session.generate_reply(instructions=INBOUND_GREETING)


if __name__ == "__main__":
    agents.cli.run_app(server)
```

**Step 3: Verify syntax**

Run:
```bash
cd /Users/lohith/Desktop/Projects/livekitlatest/agent
uv run python -c "import ast; ast.parse(open('main.py').read()); print('main.py OK')"
uv run python -c "import ast; ast.parse(open('assistant.py').read()); print('assistant.py OK')"
```
Expected: Both print OK

**Step 4: Commit**

```bash
cd /Users/lohith/Desktop/Projects/livekitlatest
git add agent/main.py agent/assistant.py
git commit -m "feat: add Truliv voice agent with inbound/outbound call handling"
```

---

### Task 6: Create Agent Dockerfile

**Files:**
- Create: `agent/Dockerfile`

**Step 1: Create Dockerfile**

Create `agent/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run the agent in start mode (production)
CMD ["uv", "run", "python", "main.py", "start"]
```

**Step 2: Commit**

```bash
git add agent/Dockerfile
git commit -m "feat: add Dockerfile for voice agent"
```

---

## Phase 3: LiveKit Server & Infrastructure Configuration

### Task 7: Create LiveKit Server Configuration

**Files:**
- Create: `deploy/livekit.yaml`

**Step 1: Create livekit.yaml**

Create `deploy/livekit.yaml`:
```yaml
# LiveKit Server Configuration for Truliv
# Docs: https://docs.livekit.io/transport/self-hosting/vm/

port: 7880
rtc:
  port_range_start: 50000
  port_range_end: 60000
  tcp_port: 7881
  use_external_ip: true

redis:
  address: localhost:6379

keys:
  # IMPORTANT: Replace these with your own generated keys before deployment
  # Generate with: docker run --rm livekit/generate generate-keys
  TRULIV_API_KEY: TRULIV_API_SECRET_REPLACE_ME

turn:
  enabled: true
  domain: turn.truliv.supercx.co
  tls_port: 443
  udp_port: 3478
  external_tls: true

logging:
  level: info
  json: true

webhook:
  urls: []

sip:
  # LiveKit SIP service configuration
  enabled: true

room:
  # Auto-close empty rooms after 60 seconds
  empty_timeout: 60
  # Max 300 participants per room (for SIP, each call = 2 participants)
  max_participants: 300
```

**Step 2: Commit**

```bash
git add deploy/livekit.yaml
git commit -m "feat: add LiveKit server configuration"
```

---

### Task 8: Create Caddy Configuration

**Files:**
- Create: `deploy/caddy.yaml`

**Step 1: Create caddy.yaml**

Create `deploy/caddy.yaml`:
```yaml
# Caddy reverse proxy configuration for LiveKit
# Handles TLS certificates automatically via Let's Encrypt

logging:
  logs:
    default:
      level: INFO

storage:
  "module": "file_system"
  "root": "/data/caddy"

apps:
  tls:
    certificates:
      automate:
        - livekit.truliv.supercx.co
        - turn.truliv.supercx.co
  layer4:
    servers:
      main:
        listen:
          - ":443"
        routes:
          - match:
              - tls:
                  sni:
                    - "turn.truliv.supercx.co"
            handle:
              - handler: tls
              - handler: proxy
                upstreams:
                  - dial:
                      - "localhost:5349"
          - match:
              - tls:
                  sni:
                    - "livekit.truliv.supercx.co"
            handle:
              - handler: tls
                connection_policies:
                  - alpn:
                      - http/1.1
                      - h2
              - handler: proxy
                upstreams:
                  - dial:
                      - "localhost:7880"
  http:
    servers:
      main:
        listen:
          - ":80"
        routes:
          - handle:
              - handler: static_response
                status_code: 301
                headers:
                  Location:
                    - "https://{http.request.host}{http.request.uri}"
```

**Step 2: Commit**

```bash
git add deploy/caddy.yaml
git commit -m "feat: add Caddy reverse proxy configuration with auto-SSL"
```

---

### Task 9: Create Redis Configuration

**Files:**
- Create: `deploy/redis.conf`

**Step 1: Create redis.conf**

Create `deploy/redis.conf`:
```
# Redis configuration for LiveKit
bind 127.0.0.1
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
save ""
appendonly no
protected-mode yes
```

**Step 2: Commit**

```bash
git add deploy/redis.conf
git commit -m "feat: add Redis configuration"
```

---

### Task 10: Create Docker Compose Configuration

**Files:**
- Create: `deploy/docker-compose.yaml`

**Step 1: Create docker-compose.yaml**

Create `deploy/docker-compose.yaml`:
```yaml
# Docker Compose for Truliv LiveKit Self-Hosted Stack
# Run: docker compose -f deploy/docker-compose.yaml up -d

services:
  redis:
    image: redis:7-alpine
    command: redis-server /etc/redis/redis.conf
    volumes:
      - ./redis.conf:/etc/redis/redis.conf
      - redis-data:/data
    network_mode: host
    restart: unless-stopped

  livekit:
    image: livekit/livekit-server:latest
    command: --config /etc/livekit.yaml
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml
    network_mode: host
    depends_on:
      - redis
    restart: unless-stopped

  caddy:
    image: livekit/caddyl4:latest
    command: run --config /etc/caddy.yaml --adapter yaml
    volumes:
      - ./caddy.yaml:/etc/caddy.yaml
      - caddy-data:/data/caddy
    network_mode: host
    depends_on:
      - livekit
    restart: unless-stopped
    cap_add:
      - NET_BIND_SERVICE

  sip:
    image: livekit/sip:latest
    network_mode: host
    depends_on:
      - livekit
    environment:
      - SIP_PORT_SIP=5060
      - SIP_PORT_MEDIA_START=50000
      - SIP_PORT_MEDIA_END=50500
      - LIVEKIT_URL=ws://localhost:7880
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
    restart: unless-stopped

  truliv-agent:
    build:
      context: ../agent
      dockerfile: Dockerfile
    network_mode: host
    depends_on:
      - livekit
    environment:
      - LIVEKIT_URL=ws://localhost:7880
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - CARTESIA_API_KEY=${CARTESIA_API_KEY}
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
      - TRULIV_API_BASE_URL=${TRULIV_API_BASE_URL}
      - TRULIV_API_KEY=${TRULIV_API_KEY}
      - SIP_TRUNK_OUTBOUND_ID=${SIP_TRUNK_OUTBOUND_ID}
      - HUMAN_TRANSFER_NUMBER=${HUMAN_TRANSFER_NUMBER}
    restart: unless-stopped

volumes:
  redis-data:
  caddy-data:
```

**Step 2: Commit**

```bash
git add deploy/docker-compose.yaml
git commit -m "feat: add Docker Compose with LiveKit, SIP, Redis, Caddy, and agent"
```

---

### Task 11: Create SIP Trunk and Dispatch Configurations

**Files:**
- Create: `deploy/sip/inbound-trunk.json`
- Create: `deploy/sip/outbound-trunk.json`
- Create: `deploy/sip/dispatch-rule.json`

**Step 1: Create inbound-trunk.json**

Create `deploy/sip/inbound-trunk.json`:
```json
{
    "trunk": {
        "name": "Truliv Inbound SIP Trunk",
        "allowed_addresses": [],
        "allowed_numbers": [],
        "auth_username": "",
        "auth_password": ""
    }
}
```
> Note: Fill in `allowed_addresses` with your SIP provider's IP addresses, and `auth_username`/`auth_password` with your SIP credentials during deployment.

**Step 2: Create outbound-trunk.json**

Create `deploy/sip/outbound-trunk.json`:
```json
{
    "trunk": {
        "name": "Truliv Outbound SIP Trunk",
        "address": "",
        "numbers": [],
        "auth_username": "",
        "auth_password": ""
    }
}
```
> Note: Fill in `address` with your SIP provider's outbound address, `numbers` with your caller ID numbers, and credentials during deployment.

**Step 3: Create dispatch-rule.json**

Create `deploy/sip/dispatch-rule.json`:
```json
{
    "dispatch_rule": {
        "rule": {
            "dispatchRuleIndividual": {
                "roomPrefix": "call-"
            }
        },
        "roomConfig": {
            "agents": [
                {
                    "agentName": "truliv-telephony-agent"
                }
            ]
        }
    }
}
```

**Step 4: Commit**

```bash
git add deploy/sip/
git commit -m "feat: add SIP trunk and dispatch rule configurations"
```

---

## Phase 4: AWS Deployment Setup

### Task 12: Create EC2 Bootstrap Script

**Files:**
- Create: `deploy/setup/init.sh`

**Step 1: Create init.sh**

Create `deploy/setup/init.sh`:
```bash
#!/bin/bash
# Truliv LiveKit Server - EC2 Bootstrap Script
# Run: sudo ./init.sh
# Tested on: Ubuntu 24.04 LTS

set -euo pipefail

echo "=== Truliv LiveKit Server Setup ==="
echo "Starting installation at $(date)"

# Update system
echo ">>> Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker
echo ">>> Installing Docker..."
apt-get install -y ca-certificates curl gnupg lsb-release
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker
systemctl enable docker
systemctl start docker

# Install LiveKit CLI
echo ">>> Installing LiveKit CLI..."
curl -sSL https://get.livekit.io/cli | bash

# Create working directory
echo ">>> Setting up LiveKit directory..."
mkdir -p /opt/livekit

echo ""
echo "=== Installation Complete ==="
echo "Next steps:"
echo "1. Copy your deploy/ folder to /opt/livekit/"
echo "2. Create .env file in /opt/livekit/ with your API keys"
echo "3. Generate LiveKit keys: docker run --rm livekit/generate generate-keys"
echo "4. Start services: cd /opt/livekit && docker compose up -d"
echo ""
```

**Step 2: Make it executable**

Run:
```bash
chmod +x deploy/setup/init.sh
```

**Step 3: Commit**

```bash
git add deploy/setup/init.sh
git commit -m "feat: add EC2 bootstrap script for Docker and LiveKit CLI"
```

---

### Task 13: Create Deployment Helper Script

**Files:**
- Create: `scripts/deploy.sh`

**Step 1: Create deploy.sh**

Create `scripts/deploy.sh`:
```bash
#!/bin/bash
# Deploy Truliv LiveKit stack to EC2
# Usage: ./scripts/deploy.sh <ec2-ip> <ssh-key-path>

set -euo pipefail

EC2_IP="${1:?Usage: ./scripts/deploy.sh <ec2-ip> <ssh-key-path>}"
SSH_KEY="${2:?Usage: ./scripts/deploy.sh <ec2-ip> <ssh-key-path>}"
REMOTE_DIR="/opt/livekit"

echo "=== Deploying Truliv LiveKit to ${EC2_IP} ==="

# Upload deployment files
echo ">>> Uploading configuration files..."
scp -i "$SSH_KEY" -r deploy/* "ubuntu@${EC2_IP}:${REMOTE_DIR}/"

# Upload agent source
echo ">>> Uploading agent source..."
scp -i "$SSH_KEY" -r agent/ "ubuntu@${EC2_IP}:${REMOTE_DIR}/agent/"

# Build and restart services
echo ">>> Building and starting services..."
ssh -i "$SSH_KEY" "ubuntu@${EC2_IP}" << 'REMOTE'
cd /opt/livekit
docker compose down || true
docker compose build
docker compose up -d
echo "Services started. Checking status..."
sleep 5
docker compose ps
REMOTE

echo ""
echo "=== Deployment complete ==="
echo "LiveKit URL: wss://livekit.truliv.supercx.co"
echo "Check logs: ssh -i ${SSH_KEY} ubuntu@${EC2_IP} 'cd /opt/livekit && docker compose logs -f'"
```

**Step 2: Make executable**

Run:
```bash
chmod +x scripts/deploy.sh
```

**Step 3: Commit**

```bash
git add scripts/deploy.sh
git commit -m "feat: add deployment helper script"
```

---

### Task 14: Create Outbound Call Test Script

**Files:**
- Create: `scripts/test-outbound.py`

**Step 1: Create test-outbound.py**

Create `scripts/test-outbound.py`:
```python
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
```

**Step 2: Commit**

```bash
git add scripts/test-outbound.py
git commit -m "feat: add outbound call test script"
```

---

## Phase 5: Step-by-Step AWS Deployment Guide

### Task 15: Write AWS Deployment Instructions (README)

This is a reference guide - not code. It documents the exact steps for the beginner user to follow.

**Files:**
- Create: `docs/plans/2026-02-17-aws-deployment-guide.md`

**Step 1: Write the deployment guide**

Create `docs/plans/2026-02-17-aws-deployment-guide.md` with complete step-by-step AWS instructions (see content in Step 1 below).

The guide covers:
1. AWS Console - Launch EC2 instance (c5.2xlarge, Ubuntu 24.04, Mumbai region)
2. Security Group configuration (all required ports)
3. Elastic IP allocation and association
4. DNS record setup (livekit.truliv.supercx.co, turn.truliv.supercx.co)
5. SSH into EC2 and run bootstrap script
6. Generate LiveKit API keys
7. Configure .env file with all API keys
8. Update SIP trunk configs with provider details
9. Start Docker Compose stack
10. Create SIP trunks and dispatch rules via LiveKit CLI
11. Test inbound and outbound calls
12. Monitoring and log commands

**Step 2: Commit**

```bash
git add docs/
git commit -m "docs: add comprehensive AWS deployment guide"
```

---

## Phase 6: Get API Keys & Final Configuration

### Task 16: Collect All Required API Keys

This is a checklist task - the user needs to sign up for services and get keys.

**Required accounts and keys:**

| Service | Sign Up URL | Key Needed |
|---------|------------|------------|
| Deepgram | https://console.deepgram.com | DEEPGRAM_API_KEY |
| Google AI Studio | https://aistudio.google.com | GOOGLE_API_KEY |
| Cartesia | https://play.cartesia.ai | CARTESIA_API_KEY |
| Google Cloud Console | https://console.cloud.google.com | GOOGLE_MAPS_API_KEY (enable Geocoding API) |

**LiveKit keys** are generated on the server:
```bash
docker run --rm livekit/generate generate-keys
```

---

## Execution Order Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | Tasks 1-2 | Project init, Python setup |
| 2 | Tasks 3-6 | Voice agent code (config, tools, agent, Dockerfile) |
| 3 | Tasks 7-11 | LiveKit infrastructure configs (server, caddy, redis, compose, SIP) |
| 4 | Tasks 12-14 | AWS scripts (bootstrap, deploy, test) |
| 5 | Task 15 | AWS deployment guide documentation |
| 6 | Task 16 | API key collection (manual) |

**Total: 16 tasks across 6 phases**

After all code tasks are complete, follow the AWS deployment guide (Task 15) to deploy to EC2.
