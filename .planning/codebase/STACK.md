# Technology Stack

**Analysis Date:** 2026-04-05

## Languages

**Primary:**
- Python (version not pinned in-repo) - backend API, simulation, and agent orchestration in `backend/main.py`, `backend/routes.py`, `backend/run_simulation.py`, and `backend/src/agents/intelligence_agent/orchestrator.py`
- JavaScript (ES modules, version not pinned in-repo) - frontend application in `frontend/src/app/page.js`, `frontend/src/hooks/useApi.js`, and related UI files

**Secondary:**
- CSS (Tailwind-driven) - styling and design tokens in `frontend/src/app/globals.css` and `frontend/tailwind.config.js`
- JSON - package/config metadata in `frontend/package.json`, `frontend/jsconfig.json`, and backend output/cache artifacts in `backend/outputs/` and `outputs/`

## Runtime

**Environment:**
- Python runtime required for backend services and simulation execution (`python main.py`, `uvicorn server:app --reload --port 8000`) documented in `README.md`
- Node.js runtime required for Next.js frontend (`npm run dev`) documented in `README.md`

**Package Manager:**
- pip - Python dependencies managed via `backend/requirements.txt`
- npm - JavaScript dependencies managed via `frontend/package.json`
- Lockfile: present for frontend (`frontend/package-lock.json`), missing for backend pip environment (no `Pipfile.lock`/`poetry.lock` detected)

## Frameworks

**Core:**
- FastAPI (`fastapi>=0.111.0`) - backend API framework used in `backend/routes.py` and exposed via `backend/server.py`
- Uvicorn (`uvicorn[standard]>=0.29.0`) - ASGI server runtime referenced in `backend/server.py`
- Next.js (`next@14.2.0`) - frontend web framework in `frontend/package.json` with app router files under `frontend/src/app/`
- React (`react@^18`, `react-dom@^18`) - UI runtime in `frontend/package.json`

**Testing:**
- Not detected (no `jest.config.*`, `vitest.config.*`, or Python test framework config files found in inspected project roots)

**Build/Dev:**
- Tailwind CSS (`tailwindcss@^3.4.0`) - utility styling configured in `frontend/tailwind.config.js`
- PostCSS (`postcss@^8`, `autoprefixer@^10`) - CSS processing in `frontend/postcss.config.js`
- ESLint (`eslint@^8`, `eslint-config-next@14.2.0`) - linting dependencies listed in `frontend/package.json`

## Key Dependencies

**Critical:**
- `openai==2.29.0` - powers LLM agent orchestration in `backend/src/agents/intelligence_agent/base_agent.py` and `backend/src/agents/intelligence_agent/orchestrator.py`
- `requests` + `beautifulsoup4` stack (`requests` imported, `bs4` used) - external data ingestion in `backend/src/agents/intelligence_agent/fetching_details.py`
- `Mesa==3.3.1`, `ortools==9.15.6755`, `PuLP==3.3.0` - simulation/optimization dependencies declared in `backend/requirements.txt` and used by simulation flow in `backend/run_simulation.py`
- `next`, `react`, `framer-motion`, `recharts`, `lucide-react` - frontend rendering and visualization stack in `frontend/package.json` and `frontend/src/app/page.js`

**Infrastructure:**
- `python-dotenv==1.2.2` - environment loading via `load_dotenv()` in `backend/src/agents/intelligence_agent/setup.py`
- `pydantic==2.12.5` - schema typing dependency for FastAPI stack in `backend/requirements.txt`
- CORS middleware from FastAPI - cross-origin setup in `backend/routes.py` for frontend origins

## Configuration

**Environment:**
- Backend environment file present: `backend/.env` (exists; contents intentionally not read)
- Frontend environment file present: `frontend/.env.local` (exists; contents intentionally not read)
- Backend loads env at import time via `load_dotenv()` in `backend/src/agents/intelligence_agent/setup.py`
- Frontend reads `NEXT_PUBLIC_API_URL` in `frontend/src/hooks/useApi.js` with fallback to `http://localhost:8000`

**Build:**
- Frontend build/runtime config files: `frontend/next.config.js`, `frontend/jsconfig.json`, `frontend/postcss.config.js`, `frontend/tailwind.config.js`
- Backend dependency config: `backend/requirements.txt`
- Repository-level run instructions: `README.md`

## Platform Requirements

**Development:**
- Python environment (venv/conda) plus pip install from `backend/requirements.txt` as directed in `README.md`
- Node/npm environment for frontend install and run (`frontend/package.json` scripts)
- Local ports used: backend `8000` (`backend/server.py`, `README.md`), frontend `3000` (`backend/routes.py` CORS allow list)

**Production:**
- Deployment target not explicitly defined in repository (no Dockerfile, no CI/CD pipeline config, and no platform manifests detected)
- Current project is configured for local process execution of FastAPI + Next.js as shown in `README.md`

---

*Stack analysis: 2026-04-05*
