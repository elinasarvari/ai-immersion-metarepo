# Agents lane: LangGraph and LLM calls (`AG-*`)

Applies to `benefit-be/packages/agents/` and the extraction and agent-success parts of `evals/`. Owner: Agents.

## Structure
- **AG-1** LangChain supplies the building blocks (model client, prompts, parsers, retrievers, MCP tools). LangGraph wires them into graphs. Both live only in `packages/agents/`.
- **AG-2** Nothing in `packages/agents/` imports `temporalio`. Each agent is a plain async function that takes `packages/domain` models and returns a domain model.
- **AG-3** One graph per agent: Intake, VerifyDocs (extract, validate, critique, then retry or escalate) and RFI drafting. Retry loops have a hard maximum, and the agent escalates once it is reached.
- **AG-4** Agents reach external systems only through MCP tools (via `langchain-mcp-adapters`) or `packages/rag`. No direct DB, file or HTTP access.

## Claude API usage
- **AG-5** Model: `claude-opus-5-5` through `langchain-anthropic`, set in one place in config. Don't hardcode model IDs anywhere else.
- **AG-6** Don't force tool choice: Claude rejects it. Use native JSON-schema structured output, or `tool_choice="auto"`.
- **AG-7** Don't set `temperature` or `top_p`.
- **AG-8** PDFs and images go to Claude directly for extraction. No separate OCR step.
- **AG-9** The model client is created once per process and reused.

## Outputs
- **AG-10** Every output is a Pydantic model validated by a structured-output parser. Free-text output is never parsed with regex.
- **AG-11** Every extracted value or claim carries its citation: a document field reference or a policy chunk ID (`PR-2`). An output without citations fails validation.
- **AG-12** Agents recommend; they never decide eligibility (`PR-1`). Low confidence or a failed validation means escalating to human review, not guessing.

## Prompts
- **AG-13** Prompts live in `packages/agents/prompts/` as versioned templates, not inline strings.
- **AG-14** User- or document-supplied text is passed as clearly delimited data, never concatenated into instructions (prompt injection, `security.md`).

## Observability
- **AG-15** Every graph run is traced to Arize Phoenix through OpenTelemetry, tagged with `case_id`.

## Tests and evals
- **AG-16** Unit tests run without Temporal, with the model client and MCP tools faked.
- **AG-17** A prompt, graph or model change runs `make eval`. The PR reports the change in extraction accuracy and agent success, and must not drop below the merge thresholds.
- **AG-18** Caseworker overrides of AI output are added to the eval set as new cases.
