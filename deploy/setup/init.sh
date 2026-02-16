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

# Add ubuntu user to docker group
usermod -aG docker ubuntu

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
