# Testing conventions
- Follow red-green-refactor: write one failing test for a single behavior before writing implementation; never write multiple tests at once in the red phase.
- Name tests behavior-first, e.g. `MethodName_Scenario_ExpectedBehavior` (or the idiomatic equivalent for the language).
- Structure every test with Arrange-Act-Assert; keep one logical outcome/assertion focus per test.
- Mock only collaborators across a boundary (DB, HTTP client, clock); never mock value objects or the class under test — prefer a hand-written fake for stateful interactions.
- Inject a fixed `Clock`/seeded `Random` for time- and randomness-dependent code; never call `now()` or an unseeded random generator directly in code under test.
- Java: JUnit 5/Jupiter + AssertJ + Mockito; unit tests as `*Test` (Surefire), integration tests as `*IT` (Failsafe). C#: NUnit with `[TestFixture]`/`[Test]` and the `Assert.That` constraint model.
- Refactor only with all tests green; rerun the full suite after every small refactor step, and address any surfaced security issue (parameterized queries, input validation, no hardcoded secrets) before merging.
