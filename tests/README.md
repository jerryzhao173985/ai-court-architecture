# Tests

## Running

```bash
# All unit tests (no API key needed, ~40s)
./venv/bin/python -m pytest tests/unit/ -v

# Single test file
./venv/bin/python -m pytest tests/unit/test_state_machine.py -v

# Integration tests (require API keys + bot credentials)
./venv/bin/python -m pytest tests/integration/ -v

# Load tests
./venv/bin/python -m pytest tests/load/ -v
```

## Directories

| Directory | Tests | Purpose |
|-----------|-------|---------|
| `unit/` | 244 | Core logic — state machine, jury voting, caching, metrics, session, evidence, case validation, bot failover, admin commands, rate limit feedback |
| `integration/` | ~15 | End-to-end Luffa flow, multi-bot setup, deliberation dynamics, admin commands |
| `load/` | 2 | Concurrent user simulation, metrics throughput |
| `analysis/` | 5 | Complexity analyzer evaluation, juror comparison |
| `property/` | — | Reserved for Hypothesis property-based tests |

## Config

`asyncio_mode = "auto"` in pyproject.toml — no need for `@pytest.mark.asyncio` on tests.
