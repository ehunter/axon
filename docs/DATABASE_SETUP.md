# Database Setup Guide

Axon uses PostgreSQL with the pgvector extension for storing brain tissue sample data and vector embeddings.

## Prerequisites

- PostgreSQL 15+ (16 recommended)
- pgvector extension

## Option 1: Docker (Recommended for Development)

The easiest way to get started is with the official pgvector Docker image:

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name axon-db \
  -e POSTGRES_USER=axon \
  -e POSTGRES_PASSWORD=axon \
  -e POSTGRES_DB=axon \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Verify it's running
docker ps
```

## Option 2: Local PostgreSQL Installation

### macOS (Homebrew)

```bash
# Install PostgreSQL 16
brew install postgresql@16

# Start PostgreSQL
brew services start postgresql@16

# Install pgvector
brew install pgvector

# Create database and user
createuser -s axon
createdb -O axon axon

# Enable pgvector
psql -d axon -c "CREATE EXTENSION vector;"
```

### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector
sudo apt install postgresql-16-pgvector

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user and database
sudo -u postgres createuser -s axon
sudo -u postgres createdb -O axon axon
sudo -u postgres psql -d axon -c "CREATE EXTENSION vector;"
```

## Configuration

1. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

2. Update the `DATABASE_URL`:

```
DATABASE_URL=postgresql+asyncpg://axon:axon@localhost:5432/axon
```

## Running Migrations

Once the database is set up:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
alembic upgrade head
```

## Verifying Setup

```bash
# Connect to database
psql -U axon -d axon

# Check pgvector is installed
\dx

# Should show:
#  Name   | Version | Schema |       Description
# --------+---------+--------+-------------------------
#  vector | 0.x.x   | public | vector data type and ivfflat access method
```

## Troubleshooting

### "role 'axon' does not exist"

Create the user:
```bash
psql -U postgres -c "CREATE USER axon WITH PASSWORD 'axon';"
```

### "database 'axon' does not exist"

Create the database:
```bash
psql -U postgres -c "CREATE DATABASE axon OWNER axon;"
```

### "extension 'vector' is not available"

Install pgvector for your PostgreSQL version. See [pgvector installation guide](https://github.com/pgvector/pgvector#installation).

### Connection refused

Check PostgreSQL is running:
```bash
pg_isready -h localhost -p 5432
```

## pgvector Performance Tuning

For production with large datasets, tune the IVFFlat index:

```sql
-- Re-create index with more lists for better recall
DROP INDEX idx_samples_embedding;
CREATE INDEX idx_samples_embedding 
ON samples USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000);  -- Increase for larger datasets

-- Set probes for queries (higher = better recall, slower)
SET ivfflat.probes = 10;
```

See [pgvector documentation](https://github.com/pgvector/pgvector#indexing) for more tuning options.

