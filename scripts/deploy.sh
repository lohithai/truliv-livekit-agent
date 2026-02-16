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
