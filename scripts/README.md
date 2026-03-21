# Scripts

## Entry Points (at project root)

| Script | Purpose |
|--------|---------|
| `play.sh` | CLI interactive trial (no API key needed) |
| `run_courtroom.sh` | Multi-bot Luffa service (production) |
| `run_luffa_bot.sh` | Single-bot Luffa service (legacy) |
| `run_server.sh` | FastAPI REST + WebSocket server |
| `run_demo.sh` | Automated CLI demo |

## Utilities (this directory)

| Script | Purpose |
|--------|---------|
| `verify_system.sh` | Full system verification checks |
| `validate_case.py` | Validate case JSON files against schema |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `setup/` | Bot registration and configuration |
| `debug/` | API connection testing |
| `demo/` | Interactive demos (fact checker, trial simulation) |

## Usage

```bash
scripts/verify_system.sh
python scripts/validate_case.py fixtures/*.json
```
