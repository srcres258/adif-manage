# AGENTS.md — adif-manage

Interactive ADIF file management tool (Python 3.8+ CLI with prompt-toolkit). Built with hatchling, src layout.

## Quick Commands

```bash
# Dev install
pip install -e .

# Run (installed)
adif-manage [file]

# Run (from source, no install)
PYTHONPATH=src python -m adif_manage [file]

# PEP 517 build
pip install build && python -m build

# Nix build
nix build

# Run all tests (pytest discovers unittest.TestCase)
pytest
pytest tests/test_adif_codec.py
pytest tests/test_adif_codec.py::TestAdifCodec::test_parse_and_write_roundtrip
pytest -k "test_parse" -v

# Type check
mypy --install-types --non-interactive src/adif_manage tests
pyright                    # uses pyrightconfig.json (overrides pyproject.toml [tool.pyright])

# Coverage
coverage run -m pytest
coverage report -m
```

**Note**: pytest, coverage, mypy, and pyright are NOT declared as dev-dependencies in pyproject.toml.
Install them separately (`pip install pytest coverage mypy pyright`).

## Project Structure

```
src/adif_manage/          # Package (src layout)
  __init__.py             # __version__ = "0.1.0" (hatch reads this for dynamic version)
  __main__.py             # main() → parses sys.argv, calls run_app()
  cli.py                  # run_cli() (testable with injectable I/O), run_app() (wires real I/O)
  commands.py             # Parse/validate commands, delete targets, aliases
  record_flow.py          # Interactive field-by-field QSO entry
  adif_codec.py           # ADI parse/serialize (pure functions, no I/O)
  storage.py              # File I/O using pathlib.Path, wraps OSError → WriteError
  models.py               # QSORecord, SessionState (mutable, not frozen)
  errors.py               # AdifManageError → AdifParseError, CommandError, WriteError
tests/
  __init__.py             # Adds src/ to sys.path (imports use `from src.adif_manage.X`)
  test_adif_codec.py
  test_command_parsing.py
  test_integration_cli.py # Tests run_cli() with injected stdin/stdout/stderr callables
  test_record_flow.py
pyproject.toml            # Build + mypy + pyright + coverage config
pyrightconfig.json        # pyright config (takes precedence over pyproject.toml [tool.pyright])
flake.nix                 # Nix package build
```

### Package entrypoints

- **`__main__.py:main()`**: CLI entrypoint. Returns `int` exit code. Parses `sys.argv[1]` as optional startup file.
- **`cli.py:run_app()`**: Creates prompt-toolkit session, calls `run_cli()` with real I/O. Returns exit code 1 if startup file can't be read.
- **`cli.py:run_cli()`**: The testable core loop. Accepts injectable `stdin_readline`, `stdout_write`, `stderr_write`, and optional `prompt_func` callables.

### Test injection pattern

`run_cli()` is the primary test surface. Tests supply lambdas for I/O:

```python
run_cli(
    state=SessionState(),
    stdin_readline=lambda: next(inputs),
    stdout_write=lambda s: output.append(s),
    stderr_write=lambda s: errors.append(s),
)
```

This pattern is used across `test_integration_cli.py` and `test_record_flow.py`.

## CLI Commands & Aliases

| Command | Aliases | Description |
|---|---|---|
| `help` | `h` | Show help |
| `list` | `ls` | List all records |
| `record` | `rec` | Interactive QSO entry |
| `read <file>` | `r <file>` | Load ADI file |
| `write <file>` | `w <file>` | Write ADI file (fails if exists) |
| `write-force <file>` | `wf <file>` | Overwrite/create parent dirs |
| `delete <n>` or `<m-n>` | `d <n>` / `d <m-n>` | Delete record(s) by 1-based index |
| `quit` | `q` | Quit (fails if dirty) |
| `quit-force` | `qf` | Force quit |

Defined in `commands.py`: `BASE_COMMANDS` + `ALIASES` dict.

## Architecture Notes

### adif_codec.py — Pure functions, no side effects

- `parse_adi(content: str) -> list[QSORecord]` — parses ADI text, raises `AdifParseError`
- `to_adi(records, adif_version, program_version) -> str` — serializes to ADI
- `missing_required_fields(fields) -> list[str]` — checks QSO_DATE, TIME_ON, CALL, MODE, FREQ/BAND
- `validate_core_field_formats(fields) -> list[str]` — validates date/time format
- ADI version hardcoded to `"3.1.7"` in `cli.py` (line 115)

### storage.py — File I/O with domain error wrapping

- `read_records(path: str) -> list[QSORecord]` — reads + parses, wraps OSError → `WriteError`
- `write_records(...)` → `WriteOutcome` — writes ADI, supports overwrite + mkdir parents
- Uses `"x"` mode for create-only, `"w"` for overwrite
- **Non-obvious**: `read_records` maps OSError to `WriteError` (not `ReadError`). This is intentional — `cli.py` catches only `WriteError` from both read and write operations.

### models.py — Mutable dataclasses

- `QSORecord` and `SessionState` are `@dataclass` (NOT frozen) — they're mutated in-place during CLI operations
- `QSORecord.normalized()` returns a new instance with uppercased keys and stripped values
- `SessionState.dirty` tracks whether in-memory state differs from disk

### Error handling convention

- **Parsing** (adif_codec): raises domain errors directly
- **Validation** (record_flow): returns error lists, caller decides
- **Storage** (storage): wraps OSError → `WriteError` with `from exc` chain
- **CLI** (cli): catches `CommandError` and `WriteError`, writes messages to stderr in Chinese

### Sequence: write command path reuse

Both `write` and `write-force` fall back to `state.last_write_path` when no argument is given. Path is remembered from last explicit write argument.

## Code Style

### Imports
- **Always** start source modules with `from __future__ import annotations` (required for Python 3.8/3.9 support of PEP 604 unions)
- Group: stdlib → third-party → relative locals (blank line between groups)
- Relative imports within package: `from .models import QSORecord`
- Tests import via `from src.adif_manage.X import Y` (enabled by `tests/__init__.py` adding `src/` to `sys.path`)

### Types & Dataclasses
- Use built-in generics: `list[str]`, `dict[str, str]`
- Use PEP 604 unions: `str | None` (not `Optional[str]`)
- Annotate all public function signatures and dataclass fields
- `@dataclass(frozen=True)` for command/value objects (`ParsedCommand`, `DeleteTarget`)
- `@dataclass` (mutable) for state objects (`QSORecord`, `SessionState`)
- `field(default_factory=...)` for mutable defaults

### Naming
- Modules/files: `snake_case`
- Functions/variables: `snake_case`
- Classes/dataclasses: `PascalCase`
- Constants: `UPPER_SNAKE`
- Private helpers: `_prefix`

### Formatting
- 4-space indentation, double quotes, f-strings
- Two blank lines between top-level definitions
- No linter or formatter configured (no ruff, black, flake8, isort, pre-commit)

## Testing

- Tests use `unittest.TestCase`; pytest discovers and runs them
- Tests import from `src.adif_manage.X` (NOT relative imports)
- Injectable I/O pattern: `run_cli()` accepts callables for stdin/stdout/stderr
- Single test case: `pytest tests/test_file.py::TestClass::test_name`
- No CI configured, no test isolation needed (no DB, no external services)

## Language

- User-facing messages: **Chinese** (e.g., "当前没有 QSO 条目", "命令输入错误")
- ADIF field names/identifiers: **English** (QSO_DATE, CALL, MODE, etc.)

## Known Config Oddities

- **Dual pyright config**: both `pyproject.toml [tool.pyright]` and `pyrightconfig.json` exist. `pyrightconfig.json` takes precedence.
- **Coverage omits phantom file**: `[tool.coverage.run] omit` lists `src/adif_manage/__about__.py` which doesn't exist — harmless, but don't create an `__about__.py` file.
