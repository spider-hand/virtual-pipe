# Virtual Pipe

A local tool that generates synthetic pipe datasets from OpenStreetMap roads. Users select an area in Japan, define custom pipe attributes, preview the generated pipes on a map, and export their attributes and geometries. The datasets are intended for product demos and import testing without using customer records.

## Coding Guidelines

### General

- Always leave one blank line between logical blocks of code for better readability.
- Document only setup that future users need to reproduce.

### Test Design

- Always separate the normal case, ties or boundary cases, invalid input, and missing data when they represent different behavior.
- Always ask before adding a test: "Would this test still make sense to a maintainer who does not know the conversation or change history?"
- Always inspect the existing tests and avoid adding another test case when the same behavior is already covered.
- Always name tests after externally observable behavior. Do not name tests after internal function calls, helper methods, or implementation structure.

### Frontend

- Always use arrow functions unless there is a specific reason to avoid them.
- Always use `@` alias instead of relative paths for imports within `client/src`.
- Always use `it("should ...")` for test cases.
- Always include one default-state test when it helps establish the baseline render in component tests; name it `should render the default state`.
- Do not assert child-component internals from parent or page tests unless the parent is explicitly responsible for the output.
- Always use `it.each(...)` when multiple meaningful inputs exercise the same behavior.
- Always use a composable for server communication instead of calling `fetch` directly.
- If the composable manages API response state, name it `use{ApiName}Query.ts` (e.g., `useUserQuery.ts`).
- Do not manually modify files inside `client/src/services/`.
- Always update locale entries for all supported languages (Japanese and English) whenever user-facing text in `client/src` is added, changed, or removed.
- Locale keys must live under and be referred to from the component or page that renders the text, even if identical wording exists elsewhere.

### Backend

- The endpoint structure should be aligned with REST API architecture.
- Name test cases after the behavior they verify, such as `test_create_user_raises_conflict_when_email_already_exists`, and avoid vague names.
- Always use `pytest.mark.parametrize` when multiple meaningful inputs exercise the same behavior.
- Always update OpenAPI schema with `drf-spectacular` after updating API and run `pnpm generate:api` at `client/` and update API client.

## Architecture Decision Records

ADRs are stored as Markdown files in `harness/context/`.

- Create an ADR only when reversing the decision would require meaningful rework or a compatibility change, the reasons for the choice are hard to infer from the code, and a future maintainer could use those reasons to make a related decision. Record the credible alternative and what the chosen approach gives up. Skip routine conventions and setup details that the code or README already explains.
- Always keep one decision per ADR.
- Use descriptive filenames (e.g., `use-osm-roads.md`).
- Always use the following format:
  - Title: A concise description of the decision.
  - Status: Proposed, Accepted, Rejected, Deprecated, or Suspended.
  - Context: What issue motivates this decision or change?
  - Decision: What are we choosing, and why did we pass over the credible alternative?
  - Consequences: What benefits, costs, or constraints does this choice introduce?
- Always check whether the decision is already documented before creating a new ADR.
- Always mark the previous ADR as Suspended, referencing its replacement when replacing a decision and creating a new one.
- Always preserve the reasoning behind the historical decisions instead of rewriting it.
