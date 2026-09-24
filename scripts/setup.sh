#!/usr/bin/env bash
set -e

echo "=== SatQuery AI — Setup Script ==="

if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

echo "Creating local data directories..."
mkdir -p data/storage
mkdir -p tests/fixtures

echo "Generating synthetic test fixtures..."
python scripts/generate_fixtures.py

echo "Setup complete! Run 'docker compose up --build' to start all services."
