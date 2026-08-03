#!/usr/bin/env bash
set -euo pipefail

# MediCheck SSL Certificate Setup (Let's Encrypt)
# Usage: ./scripts/init-letsencrypt.sh <domain>

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain.com>"
    exit 1
fi

EMAIL="${SSL_EMAIL:-admin@$DOMAIN}"

echo "=== Setting up SSL for $DOMAIN ==="

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    apt-get update && apt-get install -y certbot python3-certbot-nginx
fi

# Obtain certificate
certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --domains "$DOMAIN" \
    --redirect

# Set up auto-renewal
systemctl enable certbot.timer
systemctl start certbot.timer

echo "=== SSL setup complete ==="
echo "Certificates will auto-renew via systemd timer."
