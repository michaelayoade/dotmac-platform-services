#!/bin/bash

# Setup script for HashiCorp Vault or OpenBao
# This script configures a development Vault/OpenBao server with the required secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-"root-token"}
VAULT_VERSION=${VAULT_VERSION:-"1.15.0"}
USE_OPENBAO=${USE_OPENBAO:-"false"}

echo -e "${GREEN}DotMac Platform - Vault/OpenBao Setup${NC}"
echo "========================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to start Vault dev server
start_vault_dev() {
    echo -e "${YELLOW}Starting Vault development server...${NC}"

    if [ "$USE_OPENBAO" = "true" ]; then
        echo "Using OpenBao instead of Vault"
        if ! command_exists bao; then
            echo -e "${RED}OpenBao (bao) is not installed. Please install it first.${NC}"
            echo "Visit: https://github.com/openbao/openbao"
            exit 1
        fi

        # Start OpenBao in dev mode
        bao server -dev -dev-root-token-id="$VAULT_TOKEN" &
        VAULT_PID=$!
    else
        if ! command_exists vault; then
            echo -e "${RED}Vault is not installed. Installing Vault...${NC}"

            # Detect OS
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                if command_exists brew; then
                    brew tap hashicorp/tap
                    brew install hashicorp/tap/vault
                else
                    echo -e "${RED}Homebrew not found. Please install Vault manually.${NC}"
                    echo "Visit: https://www.vaultproject.io/downloads"
                    exit 1
                fi
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                # Linux
                wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
                echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
                sudo apt update && sudo apt install vault
            else
                echo -e "${RED}Unsupported OS. Please install Vault manually.${NC}"
                exit 1
            fi
        fi

        # Start Vault in dev mode
        vault server -dev -dev-root-token-id="$VAULT_TOKEN" &
        VAULT_PID=$!
    fi

    # Wait for Vault to start
    sleep 2

    export VAULT_ADDR="$VAULT_ADDR"
    export VAULT_TOKEN="$VAULT_TOKEN"

    echo -e "${GREEN}Vault/OpenBao started with PID: $VAULT_PID${NC}"
}

# Function to configure secrets
configure_secrets() {
    echo -e "${YELLOW}Configuring secrets...${NC}"

    # Use appropriate CLI command
    if [ "$USE_OPENBAO" = "true" ]; then
        CMD="bao"
    else
        CMD="vault"
    fi

    # Enable KV v2 secrets engine if not already enabled
    $CMD secrets enable -path=secret kv-v2 2>/dev/null || true

    # Configure application secrets
    echo "Setting up application secrets..."

    # JWT secrets
    $CMD kv put secret/jwt \
        secret_key="your-super-secret-jwt-key-change-in-production" \
        algorithm="HS256" \
        issuer="dotmac-platform" \
        audience="dotmac-api"

    # Database credentials
    $CMD kv put secret/database/postgres \
        host="localhost" \
        port="5432" \
        database="dotmac_db" \
        username="dotmac_user" \
        password="secure_password_change_me"

    # Redis credentials
    $CMD kv put secret/redis \
        host="localhost" \
        port="6379" \
        password="" \
        db="0"

    # Email service credentials (SendGrid example)
    $CMD kv put secret/email/sendgrid \
        api_key="SG.your_sendgrid_api_key_here" \
        from_email="noreply@example.com" \
        from_name="DotMac Platform"

    # SMS service credentials (Twilio example)
    $CMD kv put secret/sms/twilio \
        username="your_twilio_account_sid" \
        password="your_twilio_auth_token" \
        from_number="+1234567890"

    # Storage credentials (S3/MinIO)
    $CMD kv put secret/storage/s3 \
        access_key="minioadmin" \
        secret_key="minioadmin" \
        endpoint="http://localhost:9000" \
        bucket="dotmac-storage" \
        region="us-east-1"

    # Search service credentials (MeiliSearch)
    $CMD kv put secret/search/meilisearch \
        api_key="your_meilisearch_master_key" \
        url="http://localhost:7700"

    # Encryption keys
    $CMD kv put secret/encryption \
        fernet_key="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
        aes_key="$(openssl rand -hex 32)"

    # OAuth providers
    $CMD kv put secret/oauth/google \
        client_id="your_google_client_id" \
        client_secret="your_google_client_secret"

    $CMD kv put secret/oauth/github \
        client_id="your_github_client_id" \
        client_secret="your_github_client_secret"

    # API Keys
    $CMD kv put secret/api_keys/openai \
        api_key="sk-your-openai-api-key" \
        organization="your-org-id"

    # Monitoring and observability
    $CMD kv put secret/monitoring/sentry \
        dsn="https://your-sentry-dsn@sentry.io/project-id"

    $CMD kv put secret/monitoring/datadog \
        api_key="your_datadog_api_key" \
        app_key="your_datadog_app_key"

    echo -e "${GREEN}Secrets configured successfully!${NC}"
}

# Function to verify configuration
verify_configuration() {
    echo -e "${YELLOW}Verifying configuration...${NC}"

    if [ "$USE_OPENBAO" = "true" ]; then
        CMD="bao"
    else
        CMD="vault"
    fi

    # Test reading a secret
    if $CMD kv get -format=json secret/jwt > /dev/null 2>&1; then
        echo -e "${GREEN}✓ JWT secrets configured${NC}"
    else
        echo -e "${RED}✗ JWT secrets not found${NC}"
    fi

    if $CMD kv get -format=json secret/database/postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database secrets configured${NC}"
    else
        echo -e "${RED}✗ Database secrets not found${NC}"
    fi

    if $CMD kv get -format=json secret/encryption > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Encryption keys configured${NC}"
    else
        echo -e "${RED}✗ Encryption keys not found${NC}"
    fi
}

# Function to generate environment file
generate_env_file() {
    echo -e "${YELLOW}Generating .env.vault file...${NC}"

    cat > .env.vault <<EOF
# Vault Configuration
VAULT_ENABLED=true
VAULT_URL=$VAULT_ADDR
VAULT_TOKEN=$VAULT_TOKEN
VAULT_NAMESPACE=
VAULT_MOUNT_PATH=secret
VAULT_KV_VERSION=2

# Enable Vault features
FEATURES__SECRETS_VAULT=true
FEATURES__ENCRYPTION_FERNET=true

# Disable local secrets (use Vault instead)
JWT__SECRET_KEY=vault:jwt/secret_key
DATABASE__PASSWORD=vault:database/postgres/password
EOF

    echo -e "${GREEN}Created .env.vault file${NC}"
}

# Main execution
main() {
    echo "Configuration:"
    echo "  VAULT_ADDR: $VAULT_ADDR"
    echo "  VAULT_TOKEN: $VAULT_TOKEN"
    echo "  USE_OPENBAO: $USE_OPENBAO"
    echo ""

    # Check if Vault is already running
    if curl -s "$VAULT_ADDR/v1/sys/health" > /dev/null 2>&1; then
        echo -e "${GREEN}Vault/OpenBao is already running${NC}"
    else
        start_vault_dev
    fi

    # Configure secrets
    configure_secrets

    # Verify configuration
    verify_configuration

    # Generate environment file
    generate_env_file

    echo ""
    echo -e "${GREEN}Setup complete!${NC}"
    echo ""
    echo "To use Vault with the DotMac platform:"
    echo "1. Export environment variables:"
    echo "   export VAULT_ADDR=$VAULT_ADDR"
    echo "   export VAULT_TOKEN=$VAULT_TOKEN"
    echo ""
    echo "2. Or use the generated .env.vault file:"
    echo "   cp .env.vault .env"
    echo ""
    echo "3. Test the connection:"
    echo "   python -m dotmac.platform.secrets.test_vault"
    echo ""

    if [ ! -z "$VAULT_PID" ]; then
        echo "Vault is running with PID: $VAULT_PID"
        echo "To stop Vault: kill $VAULT_PID"
    fi
}

# Run main function
main