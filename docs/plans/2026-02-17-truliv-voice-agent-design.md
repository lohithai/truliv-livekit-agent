# Truliv Voice AI Agent - Design Document

**Date:** 2026-02-17
**Client:** Truliv (co-living/PG provider - Chennai & Bangalore)
**Status:** Approved

## Overview

Build a self-hosted LiveKit voice AI agent system on AWS for Truliv that handles both inbound customer support calls and outbound notification calls via SIP/PSTN.

## Requirements

- **Use Case:** Inbound customer support + outbound calls (rent reminders, follow-ups)
- **Channel:** Phone calls via custom SIP integration
- **Languages:** English + regional languages (Tamil, Kannada, Hindi)
- **Scale:** 50-200 concurrent calls
- **Hosting:** AWS EC2 (Mumbai region), self-hosted LiveKit (no LiveKit Cloud)
- **Domain:** truliv.supercx.co (subdomains for LiveKit and TURN)

## Architecture

### Approach: Single EC2 + Docker Compose

One EC2 instance running all services via Docker Compose, with Caddy for automatic SSL. Simplest to set up and maintain, upgradeable to multi-instance later.

### Components

| Component | Technology |
|-----------|-----------|
| WebRTC SFU | LiveKit Server (self-hosted) |
| SIP Bridge | LiveKit SIP Service |
| SSL/Proxy | Caddy (auto Let's Encrypt) |
| Message Queue | Redis |
| Voice Agent | Python (LiveKit Agents SDK) |

### AI Stack

| Component | Provider |
|-----------|---------|
| STT | Deepgram Nova |
| LLM | Google Gemini 2.5 Flash |
| TTS | Cartesia Sonic |
| VAD | Silero VAD |
| Turn Detection | MultilingualModel |
| Noise Cancellation | BVCTelephony |

### External API Integrations (Function Tools)

1. **get_properties(city, area)** - List available properties from Truliv API
2. **get_room_availability(property_id)** - Check room availability from Truliv API
3. **get_bed_availability(property_id)** - Check bed availability from Truliv API
4. **get_location(address)** - Get address/location details from Google Geolocation API

## Call Flows

### Inbound
1. Property inquiry - search and list available PGs
2. Room availability check by property
3. Bed availability check by property
4. Location/directions via Google Geolocation
5. General FAQs (pricing, amenities, rules, move-in)
6. Transfer to human agent when needed

### Outbound
1. Rent reminders
2. Follow-up calls on inquiries
3. Maintenance/policy notifications

## AWS Infrastructure

| Setting | Value |
|---------|-------|
| Instance Type | c5.2xlarge (8 vCPU, 16 GB RAM) |
| OS | Ubuntu 24.04 LTS |
| Storage | 100 GB gp3 SSD |
| Region | ap-south-1 (Mumbai) |
| Elastic IP | Yes |

### Security Group

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Admin IP | SSH |
| 80 | TCP | 0.0.0.0/0 | Certificate issuance |
| 443 | TCP+UDP | 0.0.0.0/0 | HTTPS + TURN/TLS |
| 7881 | TCP | 0.0.0.0/0 | WebRTC over TCP |
| 3478 | UDP | 0.0.0.0/0 | TURN/UDP |
| 5060 | UDP+TCP | SIP provider IP | SIP signaling |
| 50000-60000 | UDP | 0.0.0.0/0 | WebRTC + SIP media |

### DNS Records

- `livekit.truliv.supercx.co` -> A record -> EC2 Elastic IP
- `turn.truliv.supercx.co` -> A record -> EC2 Elastic IP

### Estimated Monthly Cost

- EC2 c5.2xlarge: ~$175/mo
- EBS 100GB gp3: ~$10/mo
- Elastic IP: ~$4/mo
- Data transfer: ~$45/mo
- API usage (Deepgram, Cartesia, Gemini): pay-per-use
- **Base infrastructure total: ~$234/mo + API costs**

## Project Structure

```
livekitlatest/
├── docs/plans/
├── agent/
│   ├── main.py              # Agent entry point
│   ├── assistant.py         # Truliv Assistant Agent class
│   ├── tools/               # API integration tools
│   │   ├── properties.py
│   │   ├── rooms.py
│   │   ├── beds.py
│   │   └── geolocation.py
│   ├── config.py
│   ├── prompts.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.local
├── deploy/
│   ├── docker-compose.yaml
│   ├── livekit.yaml
│   ├── caddy.yaml
│   ├── redis.conf
│   ├── sip/
│   │   ├── inbound-trunk.json
│   │   ├── outbound-trunk.json
│   │   └── dispatch-rule.json
│   └── setup/init.sh
├── scripts/
│   ├── deploy.sh
│   └── test-outbound.py
├── .env.example
└── .gitignore
```

## Key Dependencies

- Python >= 3.10
- livekit-agents ~= 1.3
- livekit-plugins: deepgram, google, cartesia, silero, noise-cancellation, turn-detector
- Docker + Docker Compose
- Caddy (reverse proxy)
