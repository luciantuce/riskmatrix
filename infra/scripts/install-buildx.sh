#!/usr/bin/env bash
# Instalează Docker Buildx pe EC2
set -e
ARCH=$(uname -m)
[ "$ARCH" = "x86_64" ] && ARCH=amd64
mkdir -p /usr/local/lib/docker/cli-plugins
curl -sSL "https://github.com/docker/buildx/releases/download/v0.19.0/buildx-v0.19.0.linux-${ARCH}" -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
echo "Buildx installed."
