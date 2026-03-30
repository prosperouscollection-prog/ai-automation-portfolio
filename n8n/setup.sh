#!/bin/bash
# Run this on the DigitalOcean droplet as root
# ssh root@<YOUR_DROPLET_IP> then paste this

set -e

echo "Installing Docker..."
apt-get update -q
apt-get install -y docker.io docker-compose-plugin curl

echo "Starting Docker..."
systemctl enable docker
systemctl start docker

echo "Creating n8n directory..."
mkdir -p /opt/n8n
cd /opt/n8n

echo "Generating secrets..."
N8N_PASSWORD=$(openssl rand -base64 16)
N8N_ENCRYPTION_KEY=$(openssl rand -base64 32)

cat > .env << EOF
N8N_PASSWORD=$N8N_PASSWORD
N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY
EOF

chmod 600 .env

echo ""
echo "=============================="
echo "SAVE THESE CREDENTIALS:"
echo "URL:      https://n8n.genesisai.systems"
echo "User:     trendell"
echo "Password: $N8N_PASSWORD"
echo "=============================="
echo ""

echo "Downloading config files..."
# Copy docker-compose.yml and Caddyfile from repo
# (paste them manually or scp from your Mac)

echo "Done. Now:"
echo "1. scp docker-compose.yml Caddyfile root@<IP>:/opt/n8n/"
echo "2. Run: docker compose up -d"
echo "3. Visit https://n8n.genesisai.systems"
