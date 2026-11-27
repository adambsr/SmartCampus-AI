# Google Stitch prompts — SmartCampus AI

These 12 self-contained prompts are the approved design batch. Use synthetic names, program examples, IDs, codes, and tokens in every reference. Each prompt requests desktop and 390 px mobile views. Keep the existing landing and staff Stitch exports as visual baselines; do not implement new screens until the user provides approved exports.

## 1. Landing refinement

> Refine the existing SmartCampus AI IIT/ISB Sfax landing reference, preserving its two-column hero, lavender-white `#faf8ff` canvas, blue `#00288e`, teal `#006a61`, white cards, campus photo, logos, Plus Jakarta Sans headings and Inter body. Make all content readable, with 16 px body, 14 px labels and 44 px controls. Keep a clear route to guest text chat and real program browsing. Shorten repeated copy, replace static program claims with catalog-compatible cards, and make the assistant preview unmistakably illustrative. Remove dead controls, false live status, decorative badges and duplicate CTAs. Show

## 2. Staff refinement

> Refine the existing SmartCampus AI staff dashboard reference, preserving its white 282 px sidebar, cool lavender canvas, blue/teal accents and Georgia staff headings. Show the signed-in role, useful role-specific navigation, logout, and a compact numeric dossier lookup for interviewers/admins. Admins may read profiles across IIT/ISB and have account management; interviewers require an interview_scheduled application. Use the labels Responsable entretiens et rendez-vous and Administrateur; no actor inheritance or institution assignment. Remove fake metrics, placeholder module cards and actions, global language selector, notification bell, health diagnostic and role badges unrelated to the current user. Use readable 16 px body, 14 px navigation, 44 px controls. Show

## 3. Login

> Design a new French SmartCampus AI IIT/ISB login screen using `#faf8ff` canvas, `#00288e` actions, `#006a61` accents, white cards, Plus Jakarta Sans headings, Inter body and 44 px controls. Include email, password, sign in, candidate registration, invited-account activation and return home. Show submitting, generic credential error, rate limit and network error without exposing account existence. Desktop and 390 px mobile; no decorative filler.

## 4. Candidate registration

> Design a new French IIT/ISB candidate registration screen in SmartCampus AI’s lavender-white, deep-blue and teal system; Plus Jakarta Sans headings, Inter body, 16 px text and 44 px controls. Include full name, email, password and 12-character guidance, submit, login and home links. Show field validation, duplicate email, submitting and success. Registration creates a candidate only; never offer role selection or automatic conversation transfer.

## 5. Invitation activation

> Design a new French SmartCampus AI invited-account activation screen with the existing lavender-white `#faf8ff`, deep blue `#00288e`, teal `#006a61`, white cards, Plus Jakarta Sans and Inter. Include invitation code, new password, 12-character guidance, activate and login. Show invalid, expired or used code, submitting and success. The code is manually delivered; use a synthetic code in the mockup.

## 6. Guest chat

> Design a new French SmartCampus AI visitor text-chat screen in the established lavender-white, blue and teal system, with readable Inter transcript, Plus Jakarta Sans title and 44 px composer controls. Include start conversation, supported chat language choice, message history and send. Show no session, empty transcript, loading, send error and expired session. Messages are stored; do not fabricate AI responses, typing indicators, citations, voice or recommendations. Include links to login/register to retain the session later.

## 7. Candidate home

> Design a new French SmartCampus AI candidate home using the lavender-white, blue and teal brand, Plus Jakarta Sans headings and Inter body. Present only the authenticated candidate’s read-only profile, actual application statuses and transferred conversation list, with clear navigation and logout. Each section needs loading, empty and error states. Do not add profile editing, new applications, QCM, appointments or invented status counts. Use synthetic data;

## 8. Candidate conversation detail

> Design a new French SmartCampus AI candidate conversation detail in the established `#faf8ff`, `#00288e`, `#006a61` system. Show a selected transferred conversation’s stored messages, timestamp, text composer, send action and back to candidate home. Include loading, empty, failed send and closed-conversation states. Do not show a fabricated assistant reply or AI typing state. Use synthetic content;

## 9. Catalog and program detail

> Design coordinated French public catalog and program-detail screens for SmartCampus AI IIT/ISB, retaining lavender-white surfaces, deep-blue actions, teal accents, Plus Jakarta Sans headings and Inter body. Catalog supports actual search, institution/level/field/language filters and pagination. Detail shows returned description, pathways, admission rules, campaign status, eligibility check and tariffs with source links. Mark unconfirmed fees and unpublished eligibility honestly; no apply button or invented prices. Include empty, loading, API error and unknown-program states.

## 10. Staff dossier

> Design a French read-only SmartCampus AI staff dossier screen using the existing staff sidebar, cool lavender canvas, deep blue/teal accents, Georgia staff headings and Inter body. Interviewers or admins arrive through a numeric ID lookup and see only profile fields returned by the authorized dossier API. Admin spans IIT/ISB; interviewer requires interview_scheduled. No private conversation history. Show loading, denied and not-found states without revealing another candidate’s data. No candidate list, editing, recommendation, interview or document controls. Use entirely synthetic candidate information;

## 11. Admin users

> Design a French SmartCampus AI admin account-management screen with the established staff shell, lavender-white/blue/teal palette, Georgia headings and Inter body. Show paginated account rows and actions to create pending staff, change interviewer/admin role and active status, and issue a one-time invitation. Include empty/loading/error and conflict states. Never allow converting a candidate to staff or imply invitation email delivery. Use synthetic users and a masked example token.

## 12. Dialogs and interaction states

> Design coordinated SmartCampus AI dialogs in `#faf8ff`, `#00288e`, `#006a61`, white surfaces and readable Inter: candidate session-wide conversation-transfer consent with unchecked checkbox and ‘not now’; admin pending-staff creation; interviewer/admin role and active-status change; one-time invitation token display with expiry and copy action; generic destructive-change confirmation. Show pending, success and recoverable failure variants, keyboard focus and 44 px actions. Use fake data only. Do not add new backend behavior.

These prompts describe the existing approved visual identity. The professor decision of 2026-11-27 supersedes actor wording in original Stitch references; this authorization refactor requires no redesign or new screens.
