# SmartCampus AI frontend

React and TypeScript interfaces for the SA-8 frontend foundation. The app contains the approved candidate/visitor landing screen and a responsible-user workspace shell, plus a reusable client for the FastAPI service.

## Prerequisites

- Node.js 22.12 or newer
- npm
- The SmartCampus AI FastAPI backend for the health diagnostic

## Install and run

From `SmartCampus-AI/frontend`:

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Vite serves the app at `http://localhost:5173`. The default frontend API URL is `http://127.0.0.1:8000`; override it with `VITE_API_BASE_URL` in `.env.local` when needed. `VITE_ACADEMIC_YEAR` supplies the academic-year label shown in the staff workspace.

Start FastAPI in another terminal from `SmartCampus-AI/backend`. The checked-in `backend/.env.example` allows `http://localhost:5173`, which matches Vite:

```powershell
uv run fastapi dev
```

The Pydantic setting’s fallback is `http://localhost:3000`; copy `backend/.env.example` to `backend/.env` if you have not configured the backend locally. No backend files are changed by this frontend.

## Commands

```powershell
npm run dev       # development server
npm run typecheck # TypeScript project check
npm run lint      # ESLint
npm run build     # type-check and production bundle
npm run preview   # serve the production bundle locally
```

## Routes

- `/` — candidate and visitor landing page with a clearly labelled, non-functional assistant preview.
- `/staff` — responsive responsible-user dashboard shell. It explains that the workspace awaits role assignment and does not enforce authentication or permissions.

## API integration status

`src/services/api` contains the configurable fetch client, typed response/error models, request-ID handling, and health service. The responsible workspace calls the backend’s implemented `GET /api/v1/health` endpoint. HTTP errors use the backend’s `{ error: { code, message, details, request_id } }` schema; network failures have a separate state. The client extracts `X-Request-ID`, falling back to the body’s `request_id`.

The broader SA-5 OpenAPI contract describes planned visitor sessions, candidate, conversation, and document routes. Those routes are not implemented by the current SA-7 backend, so this frontend does not call them or fabricate responses.

## Project structure

```text
src/
  components/
    shared/       # API diagnostic
    ui/           # reusable shadcn-style primitives
  lib/            # class-name utility
  pages/          # candidate and responsible screens
  services/api/   # typed HTTP client and health service
  App.tsx         # React Router routes
  App.css         # responsive screen styles
  index.css       # theme tokens and base styles
design-references/ # preserved Google Stitch exports
```

The UI primitives live in `src/components/ui` and follow the shadcn/ui project-owned component pattern. Lucide React supplies interface icons; Tailwind CSS is configured through its Vite plugin.

## Deferred by SA-8 scope

Authentication, protected routes, role authorization, candidate profiles, admissions operations, a live AI conversation, program data APIs, and notification behavior require backend features outside the current SA-7 implementation. The dashboard controls stay explanatory until their actual destinations exist.
