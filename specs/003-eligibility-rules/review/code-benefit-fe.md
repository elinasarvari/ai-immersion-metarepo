# Code review: benefit-fe (003-eligibility-rules)

Scope: uncommitted changes on `feature/003-eligibility-rules` (0 ahead/behind `origin/main`, merges cleanly). `tsc --noEmit` and `eslint` are clean, and the case-page and api Vitest suites pass (43 tests). The generated client matches the vendored OpenAPI file (`generated.test.ts`). No critical or major findings.

| # | Severity | File:line | Problem | Trigger | Fix |
|---|---|---|---|---|---|
| 1 | minor | src/features/caseworker/case-page/DeterminationSection.tsx:35 | Each determination's `h3` is only the result, and nothing says which one is newest. | A re-evaluated case with two determinations shows two headings such as "Ineligible" and "Eligible". A screen-reader user moving by heading can't tell which one is current. | Put the as-of or recorded date in the heading, or label the first one "Latest". |
| 2 | minor | src/features/caseworker/case-page/DeterminationSection.tsx:25 | Missing items show the raw enum code (`pay_stub`) and don't say which member or job they belong to. | Demo household C shows "pay_stub: No usable pay stub…". | Use `reasonCodeLabel(item.item)` or a label map, and name the member or job when the item has one. |
| 3 | minor | e2e/pages/DeterminationSection.ts:52 | `shownRules` and `expectedRules` compare only rule ID, threshold and outcome. FR-003-23's "inputs used" is checked only against a fixture in the unit test, never against the real API. | A backend change to the `inputs` keys would still pass e2e. | Read the Inputs cell and compare it with `rule.inputs` from the API. |
