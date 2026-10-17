# Ripple: Code Impact Analysis & Regression Engineering Platform

Ripple is an autonomous code impact analysis engine designed to answer the fundamental question every engineer faces before merging a pull request:

"If this code changes, what else could break, why might it break, and how can I verify that it still works?"

Unlike conventional CI checkers that merely run static linters, Ripple inspects unified git diffs, parses Python Abstract Syntax Trees (AST), constructs a directed call graph in memory, and traces transitive downstream dependencies from modified functions up to public HTTP routes and business-critical operations. It generates evidence-backed impact findings, isolates untested regression risks, recommends targeted pytest test suites, and executes real test suites with authentic assertion tracebacks.

---

## Core Capabilities

### 1. Deterministic AST Dependency Engine
- Parses Python source files using Python's built-in AST module to extract functions, classes, methods, decorators, and function calls.
- Maps unified diff line ranges directly to touched AST definitions to avoid guessing.
- Builds an in-memory directed dependency graph with confirmed call sites, file locations, and line numbers.

### 2. Upstream Impact & API Exposure Tracing
- Traverses the call graph upward from changed symbols to identify all callers and affected components.
- Automatically identifies public HTTP endpoints (FastAPI, Flask, Django route decorators) impacted by changes in core logic.
- Calculates deterministic risk severity (HIGH, MEDIUM, LOW) based on call depth, API exposure, and test coverage.

### 3. Truthful Test Execution & Regression Proving
- Bundles a realistic multi-module Python e-commerce sample repository (`billing`, `checkout`, `api`).
- Features a seeded regression scenario: a subtle floor truncation bug in discount calculations that passes standard tests but fails high-precision financial assertions.
- Executes pytest in an isolated subprocess with bounded timeouts and captures real assertion errors and tracebacks.
- Never fabricates test outcomes or claims unexecuted tests passed.

### 4. Public GitHub Pull Request Investigation
- Validates public GitHub pull request URLs and communicates via the official GitHub REST API.
- Downloads modified Python files and commits dynamically, maps patches, and builds the dependency graph on the fly.
- Supports optional GitHub Personal Access Tokens for private repositories and expanded rate limits.

### 5. Engineer's Workbench UI
- Technical, restrained dark aesthetic designed for active code investigation.
- Dual visual themes: Acid Lime & Forest Dark (default) and Tactical Orange & Obsidian Black.
- Interactive SVG dependency graph with pan, zoom, fit-to-view, and node selection.
- Live Evidence Inspector displaying confirmed AST call paths, direct callers, and recommended verification steps.

---

## Architecture & Technology Stack

### Backend
- Framework: Python 3.12 / Django 4.2 / Django REST Framework (DRF)
- Analysis Engine: Python built-in `ast` module, unified diff parser, and in-memory adjacency graph
- Test Runner: Pytest in a sandboxed subprocess
- HTTP Client: HTTPX
- Database: SQLite (default) with automatic PostgreSQL support via `dj-database-url`
- Static Assets: WhiteNoise for single-service deployments

### Frontend
- Framework: React 19 + TypeScript + Vite
- Styling: Custom Engineer's Workbench CSS design system with dual theme variables
- Icons: Lucide React
- Visualization: Interactive SVG node-link dependency canvas with layered hierarchical layout

---

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/api/health/` | Service health status and database connectivity |
| GET | `/api/dashboard/` | Aggregated analysis metrics and recent runs |
| POST | `/api/analyses/demo/` | Executes deterministic sample repository analysis and runs pytest |
| POST | `/api/analyses/github/` | Analyzes a public GitHub Pull Request URL |
| GET | `/api/analyses/` | Lists persisted analysis history |
| GET | `/api/analyses/<id>/` | Retrieves complete analysis report with dependency graph |
| GET | `/api/analyses/<id>/findings/` | Retrieves filterable impact findings |
| GET | `/api/analyses/<id>/tests/` | Retrieves existing tests, suggestions, and test execution results |

---

## Local Development Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Run automated test suite:
   ```bash
   python manage.py test core
   ```

6. Start development server:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open `http://localhost:5173` in your browser.

---

## Deployment Guide

### Deploying Backend to Railway

1. Connect your repository to Railway and set the root directory to `backend/`.
2. Configure the following environment variables in Railway:
   - `PORT`: `8000`
   - `DEBUG`: `False`
   - `SECRET_KEY`: `your-production-secret-key-here`
   - `ALLOWED_HOSTS`: `*`
   - `CORS_ALLOWED_ORIGINS`: `https://your-frontend.vercel.app`
   - `CSRF_TRUSTED_ORIGINS`: `https://your-frontend.vercel.app`
   - `GITHUB_TOKEN`: `optional-github-personal-access-token`
3. Database: Default SQLite runs out-of-the-box. If you add Railway's PostgreSQL plugin, `DATABASE_URL` is automatically detected with zero code changes.

### Deploying Frontend to Vercel

1. Import your repository into Vercel and set the Root Directory to `frontend`.
2. Configure the following environment variable in Vercel:
   - `VITE_API_URL`: `https://your-backend.up.railway.app`
3. Vercel automatically detects the Vite build script and deploys static assets with SPA routing rules configured in `vercel.json`.
