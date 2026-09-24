#!/usr/bin/env bash
set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "Checking Backend Health ($BACKEND_URL/health)..."
curl -s -f "$BACKEND_URL/health" | grep -q "ok" && echo "Backend is HEALTHY" || (echo "Backend is UNHEALTHY" && exit 1)

echo "Checking Frontend Health ($FRONTEND_URL)..."
curl -s -f "$FRONTEND_URL" > /dev/null && echo "Frontend is HEALTHY" || (echo "Frontend is UNHEALTHY" && exit 1)

echo "All systems operational!"
