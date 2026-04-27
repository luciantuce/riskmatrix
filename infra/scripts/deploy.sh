#!/usr/bin/env bash
# Deploy pe EC2 – din rădăcina kit-platform-v2
# Usage: bash infra/scripts/deploy.sh
# La primul run: creează .env din infra/env.example, setează URL-urile cu IP-ul serverului.

set -e
cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
  echo "No .env found. Creating .env from infra/env.example..."
  cp infra/env.example .env
  SERVER_IP=$(curl -s --max-time 3 https://ifconfig.me 2>/dev/null || curl -s --max-time 3 https://api.ipify.org 2>/dev/null || echo "localhost")
  sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$SERVER_IP:8010|" .env
  sed -i.bak "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://$SERVER_IP:3010|" .env
  rm -f .env.bak
  echo "  → .env created. URLs set to http://$SERVER_IP:3010 and :8010"
fi

if grep -q "localhost:8010\|localhost:3010" .env 2>/dev/null; then
  SERVER_IP=$(curl -s --max-time 3 https://ifconfig.me 2>/dev/null || echo "localhost")
  sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$SERVER_IP:8010|" .env
  sed -i.bak "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://$SERVER_IP:3010|" .env
  rm -f .env.bak 2>/dev/null || true
fi

echo "Building and starting containers..."
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

SERVER_IP=$(curl -s --max-time 3 https://ifconfig.me 2>/dev/null || echo "localhost")
echo "Deploy done. App: http://${SERVER_IP}:3010  API: http://${SERVER_IP}:8010/docs"
