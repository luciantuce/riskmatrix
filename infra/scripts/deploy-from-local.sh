#!/usr/bin/env bash
# Deploy de pe mașina ta: copiază codul pe EC2 și rulează deploy acolo.
#
# Usage (din rădăcina kit-platform-v2):
#   ./infra/scripts/deploy-from-local.sh ec2-user@<IP_EC2>
#
# Opțional: cheie SSH
#   KIT_V2_SSH_KEY=~/.ssh/id_ed25519 ./infra/scripts/deploy-from-local.sh ec2-user@<IP_EC2>

set -e
cd "$(dirname "$0")/../.."

TARGET="${1:?Usage: $0 ec2-user@<IP_EC2>}"
SSH_KEY="${KIT_V2_SSH_KEY:-}"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new)
[ -n "$SSH_KEY" ] && SSH_OPTS+=(-i "$SSH_KEY")

EXCLUDE_FILE=$(mktemp)
trap 'rm -f "$EXCLUDE_FILE"' EXIT
cat > "$EXCLUDE_FILE" << 'EXCLUDES'
.env
.git
node_modules
.next
__pycache__
*.pyc
.terraform
*.tfstate*
infra/terraform/.terraform
EXCLUDES

echo "Syncing kit-platform-v2 to $TARGET..."
if [ "$(uname -s)" = "Darwin" ]; then
  COPYFILE_DISABLE=1 tar -cf - -X "$EXCLUDE_FILE" . | ssh "${SSH_OPTS[@]}" "$TARGET" "mkdir -p ~/kit-platform-v2 && cd ~/kit-platform-v2 && tar xf -"
else
  tar -cf - --exclude-from="$EXCLUDE_FILE" . | ssh "${SSH_OPTS[@]}" "$TARGET" "mkdir -p ~/kit-platform-v2 && cd ~/kit-platform-v2 && tar xf -"
fi

echo "Ensuring Docker Buildx on EC2..."
ssh "${SSH_OPTS[@]}" "$TARGET" "cd ~/kit-platform-v2 && sudo bash \$(pwd)/infra/scripts/install-buildx.sh"

echo "Running deploy on EC2..."
ssh "${SSH_OPTS[@]}" "$TARGET" "cd ~/kit-platform-v2 && sudo -E bash infra/scripts/deploy.sh"

IP="${TARGET#*@}"
echo ""
echo "Done! Accesează aplicația:"
echo "  Frontend: http://${IP}:3010"
echo "  API Docs: http://${IP}:8010/docs"
