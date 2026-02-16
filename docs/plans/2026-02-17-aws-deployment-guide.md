# Truliv Voice AI Agent - AWS Deployment Guide

> Step-by-step guide for deploying the self-hosted LiveKit voice AI agent on AWS EC2.

## Prerequisites

Before starting, make sure you have:
- [ ] An AWS account (https://aws.amazon.com)
- [ ] A domain: `truliv.supercx.co` with DNS access
- [ ] API keys for: Deepgram, Google AI Studio, Cartesia, Google Maps
- [ ] Your custom SIP provider details (IP address, credentials, phone numbers)
- [ ] An SSH key pair on your local machine (or we'll create one)

---

## Step 1: Get Your API Keys

Sign up and get API keys from these services:

| Service | Sign Up URL | What You Need |
|---------|------------|---------------|
| **Deepgram** | https://console.deepgram.com/signup | API Key (for Speech-to-Text) |
| **Google AI Studio** | https://aistudio.google.com/apikey | API Key (for Gemini 2.5 Flash LLM) |
| **Cartesia** | https://play.cartesia.ai/signup | API Key (for Text-to-Speech) |
| **Google Cloud Console** | https://console.cloud.google.com | API Key with Geocoding API enabled |

Save all keys somewhere safe - you'll need them in Step 8.

---

## Step 2: Create an SSH Key Pair in AWS

1. Go to **AWS Console** → **EC2** → **Key Pairs** (left sidebar under "Network & Security")
2. Click **"Create key pair"**
3. Settings:
   - **Name:** `truliv-livekit-key`
   - **Key pair type:** RSA
   - **Private key file format:** `.pem` (for Mac/Linux)
4. Click **"Create key pair"**
5. The `.pem` file will download automatically. Save it somewhere safe.
6. On your Mac, set permissions:
   ```bash
   chmod 400 ~/Downloads/truliv-livekit-key.pem
   ```

---

## Step 3: Create a Security Group

1. Go to **EC2** → **Security Groups** (left sidebar under "Network & Security")
2. Click **"Create security group"**
3. Settings:
   - **Name:** `truliv-livekit-sg`
   - **Description:** `Security group for Truliv LiveKit voice AI server`
   - **VPC:** Leave default
4. **Inbound rules** - Click "Add rule" for each:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | SSL certificate issuance |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS + TURN/TLS |
| Custom UDP | UDP | 443 | 0.0.0.0/0 | TURN/TLS UDP |
| Custom TCP | TCP | 7881 | 0.0.0.0/0 | WebRTC over TCP |
| Custom UDP | UDP | 3478 | 0.0.0.0/0 | TURN/UDP |
| Custom UDP | UDP | 5060 | Custom (SIP provider IP/32) | SIP signaling |
| Custom TCP | TCP | 5060 | Custom (SIP provider IP/32) | SIP signaling TCP |
| Custom UDP | UDP | 50000-60000 | 0.0.0.0/0 | WebRTC + SIP media |

5. **Outbound rules:** Leave default (Allow all)
6. Click **"Create security group"**

> **Important:** Replace "SIP provider IP" with your actual SIP provider's IP address.

---

## Step 4: Launch EC2 Instance

1. Go to **EC2** → Click **"Launch instances"**
2. Settings:
   - **Name:** `truliv-livekit-server`
   - **AMI:** Ubuntu Server 24.04 LTS (Free tier eligible) - search "Ubuntu 24.04"
   - **Architecture:** 64-bit (x86)
   - **Instance type:** `c5.2xlarge` (8 vCPU, 16 GB RAM)
   - **Key pair:** Select `truliv-livekit-key` (created in Step 2)
   - **Network settings:** Click "Edit"
     - **Security group:** Select existing → `truliv-livekit-sg`
   - **Storage:** Change to `100` GiB, gp3
3. Click **"Launch instance"**
4. Wait for the instance to show "Running" status (1-2 minutes)
5. Note down the **Public IPv4 address** (e.g., `3.110.xxx.xxx`)

---

## Step 5: Allocate and Associate Elastic IP

An Elastic IP gives your server a static IP that doesn't change when you restart it.

1. Go to **EC2** → **Elastic IPs** (left sidebar under "Network & Security")
2. Click **"Allocate Elastic IP address"**
3. Click **"Allocate"**
4. Select the new Elastic IP → Click **"Actions"** → **"Associate Elastic IP address"**
5. Settings:
   - **Instance:** Select `truliv-livekit-server`
   - Click **"Associate"**
6. Note down your **Elastic IP address** (e.g., `13.234.xxx.xxx`)

---

## Step 6: Configure DNS Records

Go to your DNS provider for `truliv.supercx.co` and add these A records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `livekit.truliv.supercx.co` | Your Elastic IP (e.g., 13.234.xxx.xxx) | 300 |
| A | `turn.truliv.supercx.co` | Your Elastic IP (same IP) | 300 |

Wait 5-10 minutes for DNS to propagate. Verify with:
```bash
host livekit.truliv.supercx.co
host turn.truliv.supercx.co
```
Both should return your Elastic IP.

---

## Step 7: SSH into EC2 and Run Bootstrap

1. Open Terminal on your Mac
2. Connect to your server:
   ```bash
   ssh -i ~/Downloads/truliv-livekit-key.pem ubuntu@YOUR_ELASTIC_IP
   ```
   Type `yes` when asked about fingerprint.

3. Run the bootstrap script:
   ```bash
   # Clone or upload your project first
   # Option A: If you have git repo
   git clone YOUR_REPO_URL /tmp/truliv-agent

   # Option B: Upload from your Mac (run from another terminal)
   scp -i ~/Downloads/truliv-livekit-key.pem -r /Users/lohith/Desktop/Projects/livekitlatest ubuntu@YOUR_ELASTIC_IP:/tmp/truliv-agent
   ```

4. Run the bootstrap:
   ```bash
   sudo cp /tmp/truliv-agent/deploy/setup/init.sh /opt/
   sudo chmod +x /opt/init.sh
   sudo /opt/init.sh
   ```
   This installs Docker, Docker Compose, and LiveKit CLI. Takes ~3-5 minutes.

5. **Log out and back in** (so docker group takes effect):
   ```bash
   exit
   ssh -i ~/Downloads/truliv-livekit-key.pem ubuntu@YOUR_ELASTIC_IP
   ```

---

## Step 8: Configure the Server

1. Copy deployment files to /opt/livekit:
   ```bash
   sudo mkdir -p /opt/livekit
   sudo chown ubuntu:ubuntu /opt/livekit
   cp -r /tmp/truliv-agent/deploy/* /opt/livekit/
   cp -r /tmp/truliv-agent/agent /opt/livekit/agent
   ```

2. Generate LiveKit API keys:
   ```bash
   docker run --rm livekit/generate generate-keys
   ```
   This outputs something like:
   ```
   API Key:    APIdK4CZxxxxxxx
   API Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   **Save these! You need them below.**

3. Update LiveKit server config with your keys:
   ```bash
   nano /opt/livekit/livekit.yaml
   ```
   Replace the `keys` section:
   ```yaml
   keys:
     APIdK4CZxxxxxxx: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   Save: `Ctrl+O`, `Enter`, `Ctrl+X`

4. Create the environment file:
   ```bash
   nano /opt/livekit/.env
   ```
   Paste and fill in ALL values:
   ```bash
   # LiveKit (from step 8.2 above)
   LIVEKIT_API_KEY=APIdK4CZxxxxxxx
   LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

   # AI Services (from Step 1)
   DEEPGRAM_API_KEY=your_deepgram_key_here
   GOOGLE_API_KEY=your_google_ai_key_here
   CARTESIA_API_KEY=your_cartesia_key_here

   # Google Maps
   GOOGLE_MAPS_API_KEY=your_google_maps_key_here

   # Truliv APIs
   TRULIV_API_BASE_URL=https://api.truliv.com
   TRULIV_API_KEY=your_truliv_api_key_here

   # SIP
   SIP_TRUNK_OUTBOUND_ID=
   HUMAN_TRANSFER_NUMBER=+91xxxxxxxxxx
   ```
   Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Step 9: Configure SIP Trunks

1. Edit inbound trunk config:
   ```bash
   nano /opt/livekit/sip/inbound-trunk.json
   ```
   Fill in your SIP provider details:
   ```json
   {
       "trunk": {
           "name": "Truliv Inbound SIP Trunk",
           "allowed_addresses": ["YOUR_SIP_PROVIDER_IP"],
           "allowed_numbers": ["+91XXXXXXXXXX"],
           "auth_username": "your_sip_username",
           "auth_password": "your_sip_password"
       }
   }
   ```

2. Edit outbound trunk config:
   ```bash
   nano /opt/livekit/sip/outbound-trunk.json
   ```
   ```json
   {
       "trunk": {
           "name": "Truliv Outbound SIP Trunk",
           "address": "sip.your-provider.com",
           "numbers": ["+91XXXXXXXXXX"],
           "auth_username": "your_sip_username",
           "auth_password": "your_sip_password"
       }
   }
   ```

---

## Step 10: Start the Stack

1. Start all services:
   ```bash
   cd /opt/livekit
   docker compose up -d
   ```
   First run takes ~5 minutes (downloads images, builds agent).

2. Check all services are running:
   ```bash
   docker compose ps
   ```
   Expected: All 5 services should show "Up" status:
   - redis
   - livekit
   - caddy
   - sip
   - truliv-agent

3. Check logs for errors:
   ```bash
   # Check all logs
   docker compose logs --tail=50

   # Check specific service
   docker compose logs livekit --tail=20
   docker compose logs caddy --tail=20
   docker compose logs truliv-agent --tail=20
   ```

4. Verify SSL certificates (wait 1-2 minutes after starting):
   ```bash
   curl -I https://livekit.truliv.supercx.co
   ```
   Expected: `HTTP/2 200` or similar success response.

---

## Step 11: Register SIP Trunks and Dispatch Rules

Run these commands on the EC2 server:

```bash
# Set LiveKit CLI credentials
export LIVEKIT_URL=wss://livekit.truliv.supercx.co
export LIVEKIT_API_KEY=your_api_key
export LIVEKIT_API_SECRET=your_api_secret

# Create inbound SIP trunk
lk sip inbound create /opt/livekit/sip/inbound-trunk.json

# Create outbound SIP trunk
lk sip outbound create /opt/livekit/sip/outbound-trunk.json
# Note the trunk ID returned (e.g., ST_xxxx) - update .env SIP_TRUNK_OUTBOUND_ID with this

# Create dispatch rule (routes calls to the agent)
lk sip dispatch create /opt/livekit/sip/dispatch-rule.json
```

After getting the outbound trunk ID, update the .env:
```bash
nano /opt/livekit/.env
# Set: SIP_TRUNK_OUTBOUND_ID=ST_xxxx

# Restart the agent to pick up the new env var
docker compose restart truliv-agent
```

---

## Step 12: Test Your Setup

### Test 1: Check server health
```bash
curl https://livekit.truliv.supercx.co
```

### Test 2: List SIP trunks
```bash
lk sip inbound list
lk sip outbound list
```

### Test 3: Make a test inbound call
Call your SIP phone number from any phone. The AI agent should answer with a Truliv greeting.

### Test 4: Make a test outbound call
```bash
cd /opt/livekit
# Set env vars for the test script
export LIVEKIT_URL=wss://livekit.truliv.supercx.co
export LIVEKIT_API_KEY=your_api_key
export LIVEKIT_API_SECRET=your_api_secret

python3 agent/scripts/test-outbound.py +919876543210
```

---

## Monitoring & Maintenance

### View live logs
```bash
cd /opt/livekit
docker compose logs -f                    # All services
docker compose logs -f truliv-agent       # Agent only
docker compose logs -f livekit            # LiveKit server only
docker compose logs -f sip                # SIP service only
```

### Restart services
```bash
cd /opt/livekit
docker compose restart                    # Restart all
docker compose restart truliv-agent       # Restart agent only
```

### Update agent code
```bash
cd /opt/livekit
# Upload new agent code, then:
docker compose build truliv-agent
docker compose up -d truliv-agent
```

### Update LiveKit server version
```bash
cd /opt/livekit
# Edit docker-compose.yaml to pin version:
# image: livekit/livekit-server:v1.8.0
docker compose pull
docker compose up -d
```

### Check disk space
```bash
df -h
docker system df
```

### Clean up Docker resources
```bash
docker system prune -f
```

---

## Troubleshooting

### SSL certificates not working
```bash
# Check Caddy logs
docker compose logs caddy
# Verify DNS resolution
host livekit.truliv.supercx.co
host turn.truliv.supercx.co
# Both must resolve to your Elastic IP
```

### Agent not connecting
```bash
# Check agent logs
docker compose logs truliv-agent
# Common issues:
# - Wrong LIVEKIT_URL in .env
# - Wrong API key/secret
# - Missing API keys for Deepgram/Google/Cartesia
```

### SIP calls not connecting
```bash
# Check SIP service logs
docker compose logs sip
# Verify SIP port is open
sudo ss -tulnp | grep 5060
# Check security group allows SIP provider IP on port 5060
```

### Networking issues after reboot
```bash
# If using cloud-init and it started before networking:
sudo cloud-init clean --logs
sudo reboot now
```

### Services crash or restart
```bash
# Check which service is failing
docker compose ps
# Check the logs of the failing service
docker compose logs <service-name> --tail=100
```

---

## Cost Summary

| AWS Service | Estimated Monthly Cost |
|-------------|----------------------|
| EC2 c5.2xlarge (Mumbai) | ~$175 |
| EBS 100GB gp3 | ~$10 |
| Elastic IP | ~$4 |
| Data Transfer (~500GB) | ~$45 |
| **AWS Total** | **~$234/mo** |

Plus pay-per-use API costs:
- Deepgram STT: ~$0.0043/min
- Cartesia TTS: Check current pricing
- Google Gemini 2.5 Flash: Very affordable per-token pricing
