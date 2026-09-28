# SatQuery AI — Developer & Contributor Guide

**Project:** SatQuery AI  
**Scope:** Local Development Environment Setup, Tooling, Testing, and Contribution Guidelines  

---

## 1. Prerequisites

Before setting up SatQuery AI locally, ensure the following tools are installed:
- **Operating System:** Linux (Ubuntu 22.04+ recommended), macOS, or Windows 11 with WSL2 / Docker Desktop.
- **Python:** Python 3.11 or 3.12 (Python 3.11 recommended).
- **Node.js:** Node.js v18.x or v20.x (with `npm` v9+).
- **Docker:** Docker Engine 24+ and Docker Compose v2.20+.
- **Geospatial Binaries:** GDAL 3.6+ and PROJ (installed automatically in Docker).

---

## 2. Fast Clone & Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/SIH2026-167.git
cd SIH2026-167

# 2. Configure environment
cp .env.example .env

# 3. Create required local storage directories
mkdir -p data/storage tests/fixtures

# 4. Generate test fixtures
python scripts/generate_fixtures.py
```

---

## 3. Backend Local Setup (Standalone Mode)

If running without Docker:

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Start FastAPI server with live reloading
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger docs will be accessible at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 4. Frontend Local Setup

In a separate terminal:

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Run Next.js in development mode
npm run dev

# 3. Run production build test
npm run build

# 4. Verify TypeScript type-safety
npx tsc --noEmit
```
- Web interface will be accessible at: [http://localhost:3000](http://localhost:3000)

---

## 5. Running the Test Suite

```bash
# Run full backend regression test suite
pytest backend/tests/ -v

# Run fast unit tests in mock AI mode
AI_USE_MOCK=true pytest backend/tests/ -v

# Run targeted test suites
pytest backend/tests/test_agent.py -v
pytest backend/tests/test_grounding.py -v
pytest backend/tests/test_temporal.py -v
pytest backend/tests/test_cross_modal.py -v
pytest backend/tests/test_reports_and_ux.py -v
pytest backend/tests/test_owlvit_storage_fixes.py -v
```

---

## 6. Pre-Seeding Demo Imagery

To populate the local database and storage with satellite rasters for Demo 1 through Demo 4:
```bash
python backend/scripts/seed_demo_assets.py
```
This registers:
- `single_image`: Multi-spectral optical satellite sample for VQA and captioning.
- `grounding`: Urban scene with distinct residential and industrial structures.
- `temporal`: Pre-event $T_1$ and post-event $T_2$ acquisitions with urban development changes.
- `cross_modal`: Co-registered Cartosat optical reflectance and RISAT C-band SAR backscatter.

---

## 7. Contribution Guidelines

1. **Branch Naming:**
   - Features: `feature/short-description`
   - Bug Fixes: `fix/issue-description`
   - Documentation: `docs/topic-name`
2. **Code Style & Formatting:**
   - Python: PEP 8, typed type hints on all public functions, maximum line length 120.
   - TypeScript: Strict typing (`strict: true`), zero `any` types where models exist.
3. **Commit Messages:**
   - Use imperative present tense: `feat(agent): add support for ambiguity prompts`, `fix(storage): handle missing keys with typed 409 error`.
4. **Pull Request Checklist:**
   - [ ] All new endpoints have corresponding Pydantic schemas.
   - [ ] Backend tests pass (`pytest backend/tests/`).
   - [ ] TypeScript check passes (`npx tsc --noEmit`).
   - [ ] Documentation updated to reflect changes.
