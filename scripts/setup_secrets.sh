#!/bin/bash
# Script to set up all required secrets in Vault/OpenBao

echo "🔐 Setting up secrets in Vault/OpenBao"
echo "======================================="

# Get the Vault token
VAULT_TOKEN=$(docker logs dotmac-openbao 2>&1 | grep "Root Token:" | awk '{print $3}')
VAULT_ADDR="http://localhost:8200"

echo "Using Vault token: $VAULT_TOKEN"
echo ""

# Export for vault CLI
export VAULT_ADDR=$VAULT_ADDR
export VAULT_TOKEN=$VAULT_TOKEN

# Function to write a secret
write_secret() {
    local path=$1
    local key=$2
    local value=$3

    echo "Setting secret: $path"
    curl -s -X POST "$VAULT_ADDR/v1/secret/data/$path" \
        -H "X-Vault-Token: $VAULT_TOKEN" \
        -d "{\"data\": {\"$key\": \"$value\"}}" > /dev/null

    if [ $? -eq 0 ]; then
        echo "  ✅ $path set successfully"
    else
        echo "  ❌ Failed to set $path"
    fi
}

echo "📝 Setting application secrets..."
write_secret "app/secret_key" "value" "your-super-secret-key-change-this-in-production"

echo ""
echo "📝 Setting database secrets..."
write_secret "database/username" "value" "postgres"
write_secret "database/password" "value" "password"

echo ""
echo "📝 Setting Redis secrets..."
write_secret "redis/password" "value" "redis-password-change-in-production"

echo ""
echo "📝 Setting JWT secrets..."
write_secret "auth/jwt_secret" "value" "jwt-secret-key-change-this-in-production"

echo ""
echo "📝 Setting email/SMTP secrets..."
write_secret "smtp/username" "value" "smtp-user@example.com"
write_secret "smtp/password" "value" "smtp-password"

echo ""
echo "📝 Setting storage (MinIO/S3) secrets..."
write_secret "storage/access_key" "value" "minioadmin"
write_secret "storage/secret_key" "value" "minioadmin"

echo ""
echo "📝 Setting Vault token for renewal..."
write_secret "vault/token" "value" "$VAULT_TOKEN"

echo ""
echo "📝 Setting observability secrets..."
write_secret "observability/sentry_dsn" "value" "https://your-sentry-dsn@sentry.io/project-id"

echo ""
echo "✅ All secrets have been set!"
echo ""
echo "To verify secrets, you can read them with:"
echo "  curl -H \"X-Vault-Token: $VAULT_TOKEN\" $VAULT_ADDR/v1/secret/data/app/secret_key"