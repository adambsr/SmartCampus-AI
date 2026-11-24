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

Vite serves the app at `http://localhost:5173`. In development, requests to `/api` use the Vite proxy to reach FastAPI at `http://127.0.0.1:8000`; leave `VITE_API_BASE_URL` empty to use this same-origin proxy. `VITE_ACADEMIC_YEAR` supplies the academic-year label shown in the staff workspace.

Start FastAPI in another terminal from `SmartCampus-AI/backend`. The checked-in `backend/.env.example` allows `http://localhost:5173`, which matches Vite:

```powershell
uv run fastapi dev
```

Copy `backend/.env.example` to `backend/.env` if you have not configured the backend locally. Account login requires a distinct `ACCOUNT_JWT_SECRET`; local HTTP development also requires `AUTH_COOKIE_SECURE=false`. These settings belong in the ignored backend environment file, not the frontend `.env.local`.

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
- `/staff` — responsive responsible-user dashboard shell, now guarded by an authenticated staff role.
- `/login`, `/register`, `/activate`, `/candidate` — account flows, candidate profile/applications, and linked conversation continuation.
- `/chat` — minimal SA-25/SA-26 visitor text conversation and SA-29 hand-off to candidate consent.

## API integration status

`src/services/api` contains the configurable fetch client, typed response/error models, request-ID handling, and health service. The responsible workspace calls the backend’s implemented `GET /api/v1/health` endpoint. HTTP errors use the backend’s `{ error: { code, message, details, request_id } }` schema; network failures have a separate state. The client extracts `X-Request-ID`, falling back to the body’s `request_id`.

The frontend now includes a minimal `/chat` text conversation using SA-25/SA-26 and the SA-29 consent/transfer flow. It stores messages but does not generate assistant replies. Document and audio features remain future work. SA-29 requires the pending `0007_guest_account_link` migration before use against Neon.

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

The original SA-8 scope deferred authentication and protected routes; SA-28 now supplies them. Profile editing, admissions operations, a live AI conversation, and notifications remain future work. The dashboard modules stay explanatory until their actual destinations exist.

## SA-28 account interface

The frontend now has `/login`, `/register`, `/activate`, and a protected `/candidate`
page. `/staff` requires an authenticated responsible-user role. Access JWTs stay in
memory; on reload the client requests a fresh one with the HttpOnly refresh cookie.
Logout revokes the backend session. The development server proxies `/api` to the
local FastAPI backend so browser cookies remain on the same origin. The staff
dashboard modules remain presentation shells, while the identity and route guard
use the backend account API.

The default Neon database has the additive SA-28 migration applied. A local or
other deployment must apply migrations through `0006_account_auth` and configure
an account signing secret before these flows are usable. See
`../docs/sa28-auth-roles.md`.
