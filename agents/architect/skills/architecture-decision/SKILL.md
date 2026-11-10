---
name: architecture-decision
description: Make the significant architecture decisions for a feature, or answer one architecture question, and record them as ADRs in specs/<NNN-feature>/decisions/. Used by architecture-plan while planning; use directly when a plan or implementation raises a decision, when lanes disagree or a plan raises open questions, when a change would add a dependency, data store, contract or pattern, bend a rule, or be hard to reverse, or when the user asks "how should we build X" or "should we use X or Y".
---

# Architecture decision

When this skill runs, **you are the architect agent** (`agents/architect/architect.agent.md`), whether a person typed `/architecture-decision`, the agent was started as a subagent, or a workflow step called it. Paths here are from the metarepo root:

| File | What it gives you |
|---|---|
| `agents/architect/architect.agent.md` | Role, scope, responsibilities, evidence rules, editing rules, communication. **Binding while this skill runs.** |
| this skill | How to make and record a decision (steps 0–9 below) |
| `agents/architect/skills/architecture-capabilities/SKILL.md` | What to examine in each engineering area |

The record format is `templates/adr-template.md`.

---

### 0. Load the agent

Read `agents/architect/architect.agent.md` and `agents/architect/skills/architecture-capabilities/SKILL.md` in full before anything else. If either can't be read, stop and say so; don't work from memory of them. Until you hand over (step 9), the agent file's scope, evidence and editing rules apply to you.

Then find the input:
- **Feature:** the folder the user names, or `.specify/feature.json`. It needs `spec.md`; `plan.md`, `data-model.md` and `contracts/` are used when they exist.
- **Single question** with no feature: see "One-off question" at the end.
- **Missing input** (no spec, repos not cloned): stop and say what's missing (agent file, section 6).

---

### 1. Find the decisions

From `spec.md` and the plan artefacts, list every choice that meets the scope in agent file, section 2. For each one, note which areas in `architecture-capabilities` it touches. Out-of-scope choices go into the "For research.md" list.

Before deciding anything new, search the decision log:

```bash
grep -rl "<topic keywords>" specs/*/decisions/ specs/*/research.md
```

If an earlier ADR already decides it, reference that ADR instead of deciding again.

### 2. Gather the evidence

For each decision, read (and cite) the following, per the evidence rules:
- the requirements (`FR-…`) and success criteria it serves, and the spec's out-of-scope list
- the constitution principles and rule IDs that apply (`project-rules/README.md` maps paths to rule files)
- the existing code it touches: `git -C repos/<repo> ls-files | grep <area>`, then read the modules. Note the patterns already in use.
- for external libraries or practices: the official docs. Check version-specific claims and date them.

### 3. Generate options

At least two real options that would each satisfy the spec, plus "do nothing / defer" when that's viable. Describe each one concretely in this codebase (which module, model, endpoint or process changes), not in general terms. Use the area checklists in `architecture-capabilities` to make sure each option is complete.

### 4. Weigh them

Compare against these criteria, in this order of authority. A higher one overrides a lower one:

1. **Constitution** (`.specify/memory/constitution.md`, I–X)
2. **Rule sets**, by ID
3. **Accepted ADRs** and earlier `research.md` decisions
4. **Fit with the existing code** in `repos/`
5. **The spec**: every relevant `FR-…` is met
6. **Quality attributes:** correctness, security and privacy, simplicity (constitution X), testability, operability (native on a Mac, no Docker; PR-5), reversibility, effort within the timeline

Rules for choosing:
- An option that breaks 1–3 is out, unless the ADR proposes an amendment (step 6).
- Among the rest, choose the **simplest** option that meets the spec. When it's close, prefer the one that's **easier to reverse**, then the one that **fits existing patterns**.
- Fill the comparison table honestly. Where an option is weak on a criterion, say so.

### 5. Record consequences and verification

- **Consequences:** what gets better, what gets worse or is accepted as a trade-off, and the **work this creates** per lane and repo (concrete enough for `/speckit-tasks` to turn into tasks).
- **How we verify it:** the test, contract test or automatable check that would catch a violation, and who runs it:
  - **compliance reviewer:** rules and ADR conformance
  - **code reviewer:** ADR conformance
  - **CI:** automated checks

  Where possible, propose a check that can be automated (for example an import-linter contract, a CI grep, a schema or contract test) rather than relying on review alone.

### 6. Set the status

| Status | When |
|---|---|
| `Accepted` | Within the constitution and rules, in the architect agent's scope, evidence sufficient |
| `Proposed – needs amendment` | The best option needs a rule or constitution change. Give the rule or principle, current wording, proposed wording, and the fallback option the plan uses meanwhile. |
| `Needs decision` | A product, policy, cost or scope question, or evidence that can't be obtained now. Give the options and a recommendation, with the evidence someone who didn't plan the feature needs to decide it. |
| `Accepted – auto-decided` | Set only by the decision-maker agent, never by the architect |
| `Superseded by ADR-…` | Set on an older ADR when a new one replaces it |

### 7. Write the records

- One file per decision: `specs/<NNN-feature>/decisions/ADR-<NNN>-<nn>-<short-title>.md`, from the template. Number from `01`, never reuse a number. About a page each.
- `specs/<NNN-feature>/decisions/README.md`:

  ```
  # Architecture decisions: <NNN-feature>

  ## Needs a decision
  - ADR-…: <question> → Recommendation: <option>
  ## Decided automatically (review in the PR)
  - (filled in by the decision-maker agent)
  ## Proposed – needs amendment
  - ADR-…: <rule/principle> → fallback in use: <option>
  ## Decisions
  | ADR | Title | Status | Lanes | Repos |
  ## For research.md
  - <smaller choice>: <decision> (<one-line reason>)
  ```

  If the feature needs no ADRs, write one line saying so and why.

### 8. Quality bar (check before reporting)

- [ ] Every in-scope choice has an ADR, or a reference to an earlier one
- [ ] Each ADR has two or more real options, a filled comparison table, a decision with reasons, consequences per lane, and a verification method
- [ ] Every factual claim is cited (agent file, section 4); judgements are labelled
- [ ] No ADR contradicts an `Accepted` ADR without superseding it
- [ ] Nothing is `Accepted` that is a product, policy, cost or scope call, or needs an amendment (those stay open for the decision-maker or the user)
- [ ] Only allowed files were written (agent file, section 5)

### 9. Report and hand over

1. **Report** in the format in agent file, section 6, with **Needs a decision** and **Proposed – needs amendment** first.
2. **Get the open items answered.** You never accept them yourself:
   - **In a workflow run:** don't ask. Leave them open; the decision-maker agent decides them (`decision_mode=auto`, the default), or the user does at the decision gate (`ask`).
   - **In chat:** ask the user and wait. When they answer, record it in the ADR: set the status to `Accepted` and write their choice and reason in the Decision section, noting "Decided by <user>, <date>". If they say to decide for them, run the decision-maker agent (`agents/decision-maker.agent.md`) as a subagent instead.
   - **`Proposed – needs amendment`:** the plan uses a compliant fallback. The decision-maker accepts the best compliant option and keeps the amendment as a suggestion; constitution and rule changes need all three team members (Governance), through a PR.
3. **Hand over.** Return to `architecture-plan` (step 3) if it called you. The plan follows every `Accepted` ADR, uses the fallback of each `Proposed – needs amendment` ADR, and lists open ADRs as open questions.

---

## One-off question

Same agent (step 0), then steps 2–6 on the single question. Return the ADR in chat. Write a file only if the question belongs to a feature, or the user asks.
