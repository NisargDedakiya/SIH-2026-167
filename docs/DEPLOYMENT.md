# SatQuery AI — Deployment & Infrastructure Guide

**Project:** SatQuery AI  
**Deployment Modes:** Docker Compose (Multi-Profile: Demo, Dev, Production) & Standalone Bare-Metal  

---

## 1. Multi-Profile Docker Architecture

SatQuery AI provides three specialized Docker Compose profiles:

| Profile | Compose File | Target Use Case | Key Features |
| :--- | :--- | :--- | :--- |
| **Demo Mode** | `docker-compose.demo.yml` | SIH Evaluators & Judges | Pre-seeded satellite rasters, instant Demo Hub access, zero external downloads. |
| **Production Mode** | `docker-compose.yml` | Full Isolated Stack | PostgreSQL 16 + PostGIS 3.4, MinIO S3 Object Store, healthchecks, production builds. |
| **Developer Mode** | `docker-compose.dev.yml` | Active Development | Hot-reloading volume mounts for backend (`./backend:/app`) and frontend (`./frontend:/app`). |

---

## 2. Container Services & Port Allocation

| Container Name | Service | Image / Base | Internal Port | Host Port | Volume Mount |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `satquery_postgres` | Database | `postgis/postgis:16-3.4` | 5432 | `5432` | `postgres_data:/var/lib/postgresql/data` |
| `satquery_minio` | Object Store | `minio/minio:RELEASE.2024-03-30...` | 9000 (API), 9001 (Console) | `9000`, `9001` | `minio_data:/data` |
| `satquery_backend` | FastAPI Core Engine | `python:3.11-slim` + GDAL | 8000 | `8000` | Code / artifacts mount |
| `satquery_frontend` | Next.js 14 App | `node:18-alpine` | 3000 | `3000` | Static build / live mount |

---

## 3. Quick Start Deployment Commands

### Profile A: SIH Live Demonstration Mode (Recommended for Evaluators)
```bash
# Start all services with pre-seeded demo assets
docker compose -f docker-compose.demo.yml up --build
```
- Open Demo Hub: [http://localhost:3000/demo](http://localhost:3000/demo)

### Profile B: Full Production Mode
```bash
# Start production containers with healthcheck coordination
docker compose up --build -d

# Follow system logs
docker compose logs -f backend
```

### Profile C: Developer Mode (Live Reloading)
```bash
# Launch development stack with live volume syncing
docker compose -f docker-compose.dev.yml up --build
```

---

## 4. Health & Readiness Verification

The backend provides two distinct health probes to distinguish process liveness from dependency readiness:

1. **Liveness Probe (`/health`):**
   ```bash
   curl -s http://localhost:8000/health
   # Returns 200 OK {"status": "ok", ...}
   ```
2. **Readiness Probe (`/ready`):**
   ```bash
   curl -s http://localhost:8000/ready
   # Returns 200 OK when PostgreSQL, MinIO, and ModelRegistry are operational
   # Returns 503 Service Unavailable if any dependency is offline
   ```

---

## 5. Production Readiness Checklist

| Category | Item | Implemented in Repo | Production Requirement |
| :--- | :--- | :---: | :---: |
| **Application** | Non-root container execution | 🟡 Partial | Run container as unprivileged `appuser` |
| **Application** | Secret management | ✅ Implemented | Read via environment variables, no hardcoded secrets |
| **Application** | Masked error stack traces | ✅ Implemented | Masked with unique correlation `trace_id` |
| **Networking** | CORS domain restriction | ✅ Implemented | Configurable `CORS_ORIGINS` (no wildcards with credentials) |
| **Networking** | Security response headers | ✅ Implemented | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` |
| **Storage** | Object key randomization | ✅ Implemented | UUID keys (`images/{uuid}/original.tif`), path traversal blocked |
| **Storage** | S3 bucket isolation | ✅ Implemented | Private bucket with credentialed access |
| **Database** | Migration management | ✅ Implemented | Alembic async migrations + self-healing schema sync |
| **Infrastructure** | SSL/TLS termination | 🚧 Planned | Reverse proxy with Let's Encrypt / Nginx |
| **Infrastructure** | GPU passthrough in Docker | 🟡 Partial | Configure NVIDIA Container Toolkit (`--gpus all`) |
| **Observability** | Prometheus / OpenTelemetry | 🚧 Planned | Export metrics for cluster monitoring |
