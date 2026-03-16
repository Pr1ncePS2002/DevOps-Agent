# Testing

This document tracks test frameworks, structures, patterns, and current coverage expectations.

## Backend Validation
- **Framework:** Pytest (v8.3.4 package).
- **Structure:** All tests are located inside `apps/backend/tests/`.
- **Patterns:** Test functions start with generic prefixes like `test_health.py` and `test_unified_register.py` or `test_command_parse.py`.
- **Execution:** Test driven specifically with Pytest runners using native python assertions.
- **Mocking:** Expected use of built-in `unittest.mock` or Pytest specific monkeypatch options to prevent external system triggering (like actual Docker containers starting).

## Current Gaps & Need for Tests
- The frontend doesn't appear to have any explicit Jest or Vitest dependencies mounted yet (`package.json` relies on Next.js default setup). Addition of frontend unit testing would be a good future requirement.
- Background Jobs / Queues (`rq`) are currently removed entirely from tests based on recent cache deletions to the `worker/tasks` modules. Will need future integration testing for asynchronous queues.
