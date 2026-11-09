# Frontend rules (React + TypeScript)
- Functional components and hooks only; no class components.
- TypeScript strict mode; no `any` without a comment.
- Co-locate tests (`Component.test.tsx`) using Vitest + Testing Library.
- Data fetching lives in `src/api/`; components never call `fetch` directly.
