# SmartCampus AI frontend design specification

## Status and purpose

This is the approved design preparation brief for the next frontend batch. It defines one accessible visual system for Visiteur, Candidat, Responsable entretiens et rendez-vous (`interviewer`), and Administrateur (`admin`). The existing Stitch exports govern refinement of `/` and `/staff`; new Stitch desktop and 390 px mobile exports require review before any screen implementation. The interface copy for this batch is French. Conversation content must accommodate Arabic script and Arabizi.

The visual baseline is [`design-references/Landing Screen/screen.png`](design-references/Landing%20Screen/screen.png) and [`design-references/Espace Staff & Admin/screen.png`](design-references/Espace%20Staff%20%26%20Admin/screen.png), together with the IIT and ISB logos and campus image under `design-references/`. Preserve the identity and section hierarchy of these references while removing unsupported claims and controls. The 12 self-contained requests for Google Stitch are in [`STITCH_PROMPTS.md`](STITCH_PROMPTS.md). Use Stitch for visual exploration and approval; do not substitute ImageGen concepts.

## Current rendered baseline

Inspected the Vite frontend in headless Microsoft Edge via Playwright at **1440 × 900** and **390 × 844**. The Browser plugin was not listed, and ChatGPT Computer Use reported `browser access host is unavailable`; Playwright was the authorized fallback. Historically, a synthetic former `academic_staff` refresh response allowed read-only inspection of `/staff` without a real login, credentials, API writes, or database access. The browser reported no JavaScript page exceptions. The unauthenticated landing refresh returned the expected mocked 401. An external resource was blocked by the browser environment, so future typography review should verify font loading in the target deployment.

| Surface | Observed result | Design consequence |
|---|---|---|
| Landing desktop | The 1240 px container and two-column hero are intact. The illustrative assistant card balances the large heading. The primary blue CTA has dark label text with weak contrast. Four static program cards, repeated institutional sections, small metadata, and the closing obsolete notice remain. | Keep the two-column composition, photo, and logos; give primary actions readable contrast, shorten repetition, and make catalog discovery and guest text chat the real actions. Clearly label the assistant preview as illustrative. |
| Landing 390 px | Content fits the viewport without horizontal overflow, but the header takes two rows; the language selector and candidate link crowd the 39 px menu control. Hero lead is 12 px, and many badges, preview messages, card descriptions, and footer labels are 8–10 px. | Set a 44 px minimum target, simplify the mobile header, and raise body, labels, and metadata to the sizes below. Remove the global language selector until interface translation exists. |
| Staff desktop | The 282 px white sidebar, blue-led hero, cool canvas, and Georgia headings form a useful distinct staff identity. Placeholder module cards, multiple role badges, dead help/settings/notification actions, and a developer health panel dominate useful work. | Retain the shell and visual hierarchy; replace placeholder destinations with role-relevant work, including scoped numeric dossier lookup and admin account management. Show only the signed-in role. |
| Staff 390 px | The document scroll width is **500 px** in a **390 px** viewport. Top-bar actions extend past the right edge, making logout hard to reach. The sidebar opens, but the rest of the page remains crowded and text is often 9–13 px. | Redesign the mobile top bar and check 390 px overflow explicitly. Keep menu and logout keyboard accessible and at least 44 px tall. |

These are design findings, not claims that the current UI was fixed. Desktop and mobile screenshots were reviewed against the two stored Stitch references.

## Visual system

### Brand and color

- Preserve SmartCampus AI, IIT/ISB Sfax branding, institutional logos, campus photography, Lucide icon language, restrained gradients, rounded white cards, and the landing page's two-column hero.
- Canvas: `#faf8ff`; subtle surfaces: `#f2f3ff`, `#eaedff`, `#e2e7ff`; card: `#ffffff`.
- Main text: `#131b2e`; muted text: `#5f6578`; primary academic blue: `#00288e`; secondary blue: `#1e40af`; teal: `#006a61`; border: `#e1e3ef`; focus outline: `#4c69db`.
- Define semantic success, warning, and error tokens only for actual statuses. Do not borrow the reference files' unrelated cream and ochre suggestions or present illustrative status as live service status.
- Keep the staff screen's sidebar, blue-led hierarchy, and serif headings as a deliberate variant within this shared system.

### Typography and geometry

- Public headings: Plus Jakarta Sans. Body, navigation, forms, tables, and controls: Inter. Staff headings: existing Georgia treatment. Provide Arabic-capable fallbacks for transcript content and set its direction from the content where appropriate.
- Body and form text: **at least 16 px**. Labels and navigation: **at least 14 px**. Secondary metadata: **at least 12 px**. Preserve large display headings, readable line lengths, and natural wrapping.
- Landing content maximum: **1240 px**. Staff desktop sidebar: **282 px**. Controls: roughly **8–12 px** radius. Cards: roughly **12–17 px** radius.
- Primary controls and all icon/mobile interactive targets: **at least 44 px** high and wide where applicable. Use the existing **800 px** and **560 px** transitions as starting points; validate actual widths, especially the observed staff overflow at 390 px.
- Use consistent spacing, border, and shadow families. Keep one primary action per region and avoid decorative badge clusters.

### Components and behavior

- Extend the project's existing shadcn-style Button, Card, and Badge primitives where needed with fields, dialogs, alerts, skeletons, empty states, and true status variants. Follow the installed shadcn project configuration and existing React/Vite/Tailwind v4 conventions. Do not introduce a parallel UI stack.
- Every apparent control must navigate to an implemented route or call an implemented endpoint. A disabled or illustrative element must look and read as such. Remove obsolete notice actions, fake metrics, decorative controls, and unavailable modules.
- Show loading, empty, error, and success states where applicable. Use explicit field labels, visible focus, keyboard-operable dialogs, adequate contrast, and reduced-motion support. Preserve scroll position and focus sensibly through state changes.
- Keep independent data sections independent so one failed request does not obscure successful sections. Avoid unnecessary request waterfalls and duplicate fetching when implementing later.
- Use synthetic names, program examples, IDs, codes, and tokens in Stitch. Never include real credentials or candidate data.
- Do not present SA-5's future profile editing, document, or audio routes as working features. No simulated assistant answer, recommendation, application submission, QCM, appointment, or interview action.

## Screen inventory and functional boundaries

| Design status and screen | User, information, and working action | Required states and boundary |
|---|---|---|
| **Refine** `/` landing | Public IIT/ISB identity, real program discovery, links to catalog, guest chat, and account access. | Catalog loading, empty, and error; remove obsolete chat notice, false live status, static program claims, and decorative controls. |
| **Refine** `/staff` dashboard | Signed-in interviewer or admin identity and role; relevant destinations and logout; numeric dossier lookup for both roles. | Role-specific content; lookup loading, denied, and not found; no fake metrics or unavailable modules. Admins read any candidate profile; interviewers require interview_scheduled. |
| **Redesign** `/login` | Candidate or staff email/password via auth API. | Submitting, generic invalid credentials, rate limit, network error, success redirect; do not disclose account existence. |
| **Redesign** `/register` | Public candidate signup with full name, email, password. | Validation, duplicate email, submitting, success, and possible later transfer offer; registration creates candidates only. |
| **Redesign** `/activate` | Invited staff token and first password. | Invalid, expired, or used token; submitting and success; manually delivered code, no automated email claim. |
| **Redesign** `/chat` | Visitor starts a session, chooses a supported conversation language, reads and stores text messages. | No session, restore, empty transcript, sending, expired session, and error. State clearly that AI replies are unavailable. |
| **Redesign** `/candidate` | Candidate's own read-only profile, application statuses, and transferred conversation list. | Independent loading, empty, and error for each section; no edit, application submission, or QCM action. |
| **Redesign** candidate conversation detail | Candidate retrieves and appends text to a transferred conversation. | Loading, empty, send failure, closed conversation; no simulated assistant reply. |
| **Create** catalog and program detail | Public search, institution/level/field/language filters, pagination, pathways, admission rules, campaigns, eligibility, and published tariffs. | Search empty/error, unknown program, unpublished eligibility, unconfirmed or unpublished fees; cite returned source URLs; no apply button. |
| **Create** staff dossier | Interviewer or admin reads only the candidate profile returned by authorized `GET /candidates/{id}`; interviewer access requires interview_scheduled and admin access spans IIT/ISB. | Direct numeric ID lookup, loading, 403, 404; no staff candidate list, recommendation, interview action, document control, or edit. |
| **Create** admin users | Admin lists accounts, creates pending staff, changes allowed staff role/status, and issues a one-time activation invitation. | Empty/loading/error, validation/conflict, success, and one-time token display; no candidate-to-staff conversion or email-delivery claim. |

Conversation transfer additionally needs a **candidate consent dialog or panel**: unchecked consent, “not now,” pending, success, expiry, and failure. Preserve session-wide transfer and verified ownership proof. Admin creation, role/status changes, and one-time invitation display each need separate dialog designs. An explicit confirmation design may cover a genuinely destructive change. No database or authentication behavior changes are authorized by this brief.

## API and content guardrails

- Connect later implementation only to endpoints actually present in the backend. The implemented scope includes public catalog, admission, eligibility, tariffs, and campaigns; scoped staff dossier reads; admin account management; auth; visitor text sessions and messages; candidate read-only account/application data; and consent-based transfer.
- The SA-5 OpenAPI file includes planned profile editing, documents, and audio routes that the backend does not implement. Do not infer availability from the contract alone.
- Preserve existing role checks, visitor credentials, account authentication, and transfer semantics. Interviewer access requires interview_scheduled; admin dossier access spans institutions; frontend role presentation does not replace authorization.
- The global interface remains French until real translation exists. A conversation language choice can be shown in chat because it affects conversation content, not page translation. Allow Arabic and Arabizi messages in the transcript.
- Candidate applications remain status-only until submission APIs exist. Staff dossier entry uses numeric ID because there is no staff list/search API.

## Stitch review and later implementation gate

Generate the 12 desktop and 390 px mobile screen/dialog sets from `STITCH_PROMPTS.md`. Review landing and staff as refinements of the stored exports. Reject outputs that alter their brand identity, lose the landing two-column hero or staff shell, introduce tiny type or mobile overflow, or suggest unsupported features. Review loading, empty, error, consent, and admin token states as part of the same design batch.

After the user supplies approved Stitch exports, implement shared tokens/components in the existing React/Vite/shadcn-style stack and connect only implemented APIs. Then compare rendered desktop and mobile views with approved exports and verify role redirects, API success/error/empty/loading states, catalog semantics, guest and candidate text chat, explicit transfer consent, staff 403/404, admin conflicts, focus, keyboard use, text readability, typecheck, lint, and build. **This file does not authorize implementation of the new screens before those exports arrive.**

## Approved actor simplification 2026 11 27

Preserve the approved layouts and visual tokens. The two professional labels are “Responsable entretiens et rendez-vous” and “Administrateur”; both use the existing dossier lookup. Only admin sees account management, with interviewer/admin role choices and no institution assignment controls. institution_id remains nullable API compatibility metadata. No professional actor inherits the other. Original Stitch exports are retained as historical visual references; their obsolete actor copy is superseded by this section.

The dossier is read-only profile data. Do not add candidate lists, conversation summaries/transcripts, QCM, interview outcomes, appointments, appointment invitations, recommendation review, RAG/configuration, program administration or statistics. Those are future UML responsibilities. Account activation invitations remain manually delivered and operate as before, with unused invitations revoked on effective access changes.
