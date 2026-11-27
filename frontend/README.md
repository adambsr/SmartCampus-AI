# SmartCampus AI frontend

React, TypeScript, Vite, Tailwind CSS, and project-owned shadcn-style components for the SmartCampus AI web application. The frontend connects to the FastAPI APIs for catalog data, visitor and candidate conversations, candidate profiles and applications, and staff account management.

## Prerequisites

- Node.js 22.12 or newer
- npm
- The FastAPI backend for API-backed screens

## Install and run

From `frontend/`:

```powershell
npm install
Copy-Item .env.example .env.local  # optional; configure only when needed
npm run dev
```

Vite serves the app at `http://localhost:5173`. In development, `/api` requests are proxied to FastAPI at `http://127.0.0.1:8000`; leave `VITE_API_BASE_URL` empty to use the proxy. The backend CORS settings should allow `http://localhost:5173` when calling it directly.

## Commands

```powershell
npm run dev       # development server
npm run typecheck # TypeScript project check
npm run lint      # ESLint
npm run build     # type-check and production bundle
npm run preview   # serve the production bundle locally
```

## Routes

| Route | Access | Screen |
| --- | --- | --- |
| `/` | Public | Landing page with links to the catalog and visitor chat |
| `/catalog` | Public | Searchable academic program catalog |
| `/programs/:code` | Public | Program details, published admission data, eligibility check, campaign, and sourced tariffs |
| `/chat` | Public | Visitor text session and conversation storage; assistant replies are not generated |
| `/login` | Public | Sign in |
| `/register` | Public | Candidate registration |
| `/activate` | Public | Staff account activation using an invitation token |
| `/candidate` | Candidate | Candidate profile, applications, linked conversations, and transfer consent |
| `/candidate/conversations/:id` | Candidate | Read and continue an associated conversation |
| `/staff` | Staff | Staff workspace and candidate dossier lookup |
| `/staff/dossiers` and `/staff/dossiers/:id` | Academic staff or interviewer | Candidate dossier lookup and read-only dossier |
| `/staff/users` | Admin | Staff account management, provisioning, and invitations |

Protected routes enforce account roles in the frontend and rely on backend authorization for data access. Candidate registration and staff activation use the authentication API. Admin invitations are displayed once for manual delivery; the application does not send invitation email.

## API and data behavior

Typed API clients are in `src/services/api/`. The catalog screens load real program, admission, eligibility, campaign, and tariff responses. Candidate and staff screens use the profile, application, conversation, dossier, and admin APIs. Empty or unpublished backend data is shown as such; illustrative Stitch values are not used as production data.

Visitor session credentials remain in tab `sessionStorage`. A signed-in candidate can explicitly consent to transfer the entire visitor session and its conversations to their account. Transfer invalidates that visitor session. The visitor chat stores text messages but does not produce assistant responses. See [SA-29 conversation transfer](../docs/sa29-guest-account-link.md).

The frontend does not access the database directly. Configure backend secrets and database settings in the backend environment file as described in the [backend guide](../backend/README.md). The configured Neon database was confirmed at migration `0007_guest_account_link` on 2026-11-27. Other database environments must apply that migration before transfer works; the frontend does not apply migrations.

## Design and structure

The approved visual system and screen requirements are documented in [DESIGN.md](DESIGN.md) and [STITCH_PROMPTS.md](STITCH_PROMPTS.md).

```text
src/
  components/shared/ # auth context, role shells, dialogs, and shared states
  components/ui/     # reusable UI primitives
  pages/             # public, candidate, staff, and admin routes
  services/api/      # typed API clients
  App.tsx            # React Router routes and role gates
  sc.css             # shared screen styles and design tokens
  index.css          # base styles and fonts
```

Lucide React supplies interface icons. Tailwind CSS is configured through its Vite plugin; shared controls follow the project-owned shadcn component pattern.
