# Frontend lane: benefit-fe (`FE-*`)

Applies to the whole `benefit-fe` repo. Owner: Platform & UI. [frontend-react.md](frontend-react.md) also applies, except as noted below.

## Stack
- **FE-1** React with TypeScript (strict), Vite and `pnpm`. Styling with Tailwind CSS and shadcn/ui. Charts with Recharts.
- **FE-2** This is a client-side app built with Vite, with no server rendering. Ignore the Server Components and `'use client'` rules in `frontend-react.md`.

## Data and API
- **FE-3** The API client is generated from `benefit-be`'s OpenAPI spec with `openapi-typescript`. Never hand-write API types or edit generated files.
- **FE-4** All server data goes through TanStack Query hooks in `src/api/`. Components don't call `fetch` and don't keep server data in local state.
- **FE-5** Query keys include the case ID. Mutations invalidate the affected queries.

## Apps and access
- **FE-6** There are two areas: the caseworker console and the applicant portal. Routes are guarded by the JWT role (`applicant`, `caseworker`, `supervisor`). The UI hides what a role can't do, but the API still enforces it.
- **FE-7** AI-generated content is labelled as AI-assisted, shows its citations (document field or policy chunk), and lets a caseworker override it. An override records a reason.
- **FE-8** The metrics page reads metrics from the API. It doesn't compute them in the browser.

## UI quality
- **FE-9** Use shadcn/ui components before writing custom ones. Meet WCAG 2.1 AA.
- **FE-10** Every page handles its loading, empty and error states.

## Checks and tests
- **FE-11** ESLint, Prettier and `tsc --noEmit` pass. `pnpm audit` shows no high or critical issues.
- **FE-12** Component tests use Vitest and Testing Library. Every user journey (applicant submits, caseworker reviews, supervisor overrides) has a Playwright end-to-end test.
- **FE-13** Fixtures and screenshots use synthetic data only (`PR-3`).
