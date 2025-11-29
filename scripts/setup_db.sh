#!/bin/bash
# Database setup script for Axon
# This script creates the PostgreSQL database and user, and enables pgvector

set -e

# Configuration (override with environment variables)
DB_NAME="${AXON_DB_NAME:-axon}"
DB_USER="${AXON_DB_USER:-axon}"
DB_PASSWORD="${AXON_DB_PASSWORD:-axon}"
DB_HOST="${AXON_DB_HOST:-localhost}"
DB_PORT="${AXON_DB_PORT:-5432}"

echo "🧠 Axon Database Setup"
echo "======================"
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on $DB_HOST:$DB_PORT"
    echo ""
    echo "Please start PostgreSQL first:"
    echo "  - macOS (Homebrew): brew services start postgresql@16"
    echo "  - Linux: sudo systemctl start postgresql"
    echo "  - Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres pgvector/pgvector:pg16"
    exit 1
fi

echo "✓ PostgreSQL is running"

# Create user if it doesn't exist
echo "Creating user '$DB_USER'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Create database if it doesn't exist
echo "Creating database '$DB_NAME'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Grant privileges
echo "Granting privileges..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Enable pgvector extension
echo "Enabling pgvector extension..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo ""
echo "✅ Database setup complete!"
echo ""
echo "Connection string:"
echo "  postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Next steps:"
echo "  1. Add this to your .env file:"
echo "     DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "  2. Run migrations:"
echo "     alembic upgrade head"

