---
name: SmartCampus AI
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#444653'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#757684'
  outline-variant: '#c4c5d5'
  surface-tint: '#3755c3'
  primary: '#00288e'
  on-primary: '#ffffff'
  primary-container: '#1e40af'
  on-primary-container: '#a8b8ff'
  inverse-primary: '#b8c4ff'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#532a00'
  on-tertiary: '#ffffff'
  tertiary-container: '#743d00'
  on-tertiary-container: '#ffa85d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b8c4ff'
  on-primary-fixed: '#001453'
  on-primary-fixed-variant: '#173bab'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system establishes an academic-tech standard tailored for higher education institutions in North Africa. It projects institutional credibility, rigorous academic authority, and forward-looking technological intelligence. The emotional goal is to evoke reassurance, clarity, and empowerment for students, faculty, and administrative researchers navigating academic workflows, intelligent schedules, and bilingual communication portals.

The aesthetic philosophy balances **Corporate / Modern** precision with warm Mediterranean hospitality. Crisp white surfaces and deep academic blues are grounded by gentle desert sand undertones, avoiding the sterile detachment of pure Silicon Valley aesthetics while maintaining high utilitarian legibility. Visuals favor structural clarity, measured whitespace, subtle low-contrast boundaries, and clean geometric rhythm that gracefully accommodates multi-script layout shifts (Latin and Arabic scripts).

## Colors

The color architecture is built around authoritative institutional presence tempered by warmth:

- **Primary (`#1E40AF`)**: Deep institutional cobalt blue. Serves as the primary operational anchor, interactive focus, and header prominence. Used for active navigation, primary action buttons, key metrics, and brand markers.
- **Secondary (`#0D9488`)**: Mediterranean sea-pine teal. Denotes AI system actions, automated insights, real-time sync indicators, and smart schedule confirmations.
- **Tertiary (`#D97706`)**: Sfax golden ochre/sand. Reserved for alerts, deadline notices, academic grade warnings, and warm contextual highlights.
- **Neutral (`#0F172A`)**: Deep midnight slate. Employs varying opacities for text hierarchies, micro-borders, and structurally grounded container strokes.

### Tonal Foundation & Canvas
- **Base Canvas**: `#FAF9F6` (Alabaster cream-sand) creates a warm, eye-fatigue-reducing Mediterranean base rather than stark digital white.
- **Surface Elevation**: `#FFFFFF` for primary content cards and interactive dialogs.
- **Subtle Surface Container**: `#F1F5F9` (Slate mist) for table headers, inactive segments, and structural card groupings.
- **Border Tone**: `#E2E8F0` with 70% to 100% opacity for clean, hairline borders.

## Typography

Typography balances academic authority with geometric digital legibility:

- **Headlines & Display**: Set in **Plus Jakarta Sans**, offering a modern humanist presence with geometric balance, welcoming apertures, and high readability for executive dashboards and institutional course catalogs.
- **Body & Data**: Set in **Inter**, ensuring optimal performance across variable density tables, multilingual text, grades, code snippets, and conversational AI transcripts.
- **Multilingual & Script Harmonization**: Inter and Plus Jakarta Sans are tuned to align seamlessly with system Arabic fallbacks (such as Noto Sans Arabic or Segoe UI) in line-height calculation and baseline alignment, accommodating code-switching between French, Modern Standard Arabic, and Arabizi without baseline distortion or truncation.
- **Line Heights**: Kept relaxed (`1.5` to `1.6`) on body copy to preserve vertical clarity when rendering complex academic syllabi and diacritics.

## Layout & Spacing

The layout is structured on an 8-point base grid using a responsive fluid column approach:

- **Desktop (1024px and above)**: 12-column grid, `margin: 2rem` (max-width bounded to 1440px for dashboards, 1200px for reading views), `gutter: 1.5rem`.
- **Tablet (768px – 1023px)**: 8-column grid, `margin: 1.5rem`, `gutter: 1.25rem`. Split views transition from horizontal side-by-side to collapsible drawer sidebars.
- **Mobile (below 768px)**: 4-column fluid layout, `margin-mobile: 1rem`, `gutter-mobile: 1rem`. Data-heavy academic schedules convert into stacked chronological cards.

Component padding strictly observes the `space-*` tokens:
- Use `space-xs` and `space-sm` for inline badges, button paddings, and metadata chips.
- Use `space-md` for standard card interiors, form field gaps, and list group rows.
- Use `space-lg` and `space-xl` for dashboard module separation and modal padding.

## Elevation & Depth

Visual hierarchy is maintained primarily through **low-contrast outlines combined with subtle ambient shadows** rather than dramatic layered drops. This avoids visual clutter across dense academic portals:

- **Level 0 (Flat / Canvas)**: Background `#FAF9F6`. No border, no elevation.
- **Level 1 (Card / Container)**: Pure white background `#FFFFFF`, surrounded by a 1px solid hairline border (`#E2E8F0`). Shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04)`.
- **Level 2 (Hover / Floating Cards / Dropdowns)**: Background `#FFFFFF`, border `#CBD5E1`. Shadow: `0 4px 6px -1px rgba(30, 64, 175, 0.06), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`. Noticeable subtle blue ambient cooling in the shadow.
- **Level 3 (Modals / Overlays / AI Assist Panels)**: Background `#FFFFFF`, hairline border `#94A3B8`. Shadow: `0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`.

## Shapes

The design system adopts **Roundedness Level 2** (`0.5rem` / `8px` standard radius). This bridges contemporary academic tradition with an approachable digital feel:

- **Base Elements (`0.5rem` / `8px`)**: Buttons, text inputs, dropdown triggers, and tabular rows.
- **Cards & Containers (`rounded-lg` / `1rem` / `16px`)**: Course cards, timetable blocks, AI summary sheets, and modal dialogues.
- **Hero & Feature Banners (`rounded-xl` / `1.5rem` / `24px`)**: Institutional announcement banners and top-level module wrappers.
- **Pill Elements (`9999px`)**: Status tags, AI prompt suggestions, and attendance badges.

## Components

### Buttons
- **Primary**: Solid Cobalt (`#1E40AF`) with white text, `0.5rem` radius, `0.5rem 1.25rem` padding. Active scale `0.98`. Focus ring: 2px solid `#1E40AF` offset by 2px.
- **Secondary**: Surface white with 1px border (`#E2E8F0`) and text (`#0F172A`). Hover transitions to background `#F8FAFC` and border `#CBD5E1`.
- **AI Assist**: Subtle gradient background (`#1E40AF` to `#0D9488`) with high-contrast white text for AI-powered actions (e.g., "Summarize Syllabus", "Translate Schedule").

### Input Fields
- Height: 44px for accessible touch targets.
- Base style: `#FFFFFF` fill with 1px hairline border (`#CBD5E1`), `0.5rem` radius, typography `body-md`.
- Focus state: Border transitions to `#1E40AF` with a soft ambient outline (`0 0 0 3px rgba(30, 64, 175, 0.15)`).
- RTL support: Dynamic label alignment and directional icon placement for Arabic input.

### Cards
- Pure white (`#FFFFFF`) surface, 16px corner radius (`rounded-lg`), hairline border (`#E2E8F0`), padded with `space-lg`.
- Hover state: Subtle lift (`-2px` vertical translation) with Level 2 blue-tinted ambient shadow.

### Chips & Tags
- Height: 26px, pill-shaped (`9999px`), typography `label-sm`.
- Attendance / Verified Chip: Background `#ECFDF5` with text `#065F46` and 1px border `#A7F3D0`.
- AI Generated Tag: Background `#F0FDFA` with teal text (`#0F766E`) and a micro sparkles icon.

### Checkboxes & Radio Buttons
- 18px x 18px with `0.25rem` radius for checkboxes; fully circular for radios.
- Unchecked: 1.5px border (`#94A3B8`) on transparent background.
- Checked: `#1E40AF` fill with crisp white checkmark/dot.

### Contextual Academic Components
- **Bilingual Grade Transcript Row**: Two-column responsive row showing course titles in French and Arabic with right-aligned numeric score pills.
- **AI Prompt Assistant Ribbon**: Docked conversational chip bar featuring pre-formulated prompts for university bureaucracy, course registration deadlines, and library reservations.