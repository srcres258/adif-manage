# AGENTS.md — adif-manage

Interactive ADIF file management tool. Python 3.9+ CLI package using hatchling.

## Build / Run

```bash
pip install build && python -m build     # PEP 517 build
nix build                                # Nix build
pip install -e .                         # Dev install
adif-manage [file]                       # Installed entrypoint
PYTHONPATH=src python -m adif_manage [file]  # From source
```

## Test Commands

Test runner: **pytest** (tests use `unittest.TestCase` but pytest discovers and runs them).

```bash
pytest                                              # All tests
pytest tests/test_adif_codec.py                     # Single file
pytest tests/test_adif_codec.py::TestAdifCodec::test_parse_and_write_roundtrip  # Single case
python -m unittest tests.test_adif_codec.TestAdifCodec.test_parse_and_write_roundtrip  # Via unittest
pytest -k "test_parse"                              # Keyword filter
pytest -v                                           # Verbose
```

## Type Checking

```bash
# mypy (command from pyproject.toml hatch env)
mypy --install-types --non-interactive src/adif_manage tests

# pyright (uses pyrightconfig.json)
pyright
```

## Coverage

```bash
coverage run -m pytest
coverage report -m
```

No linter or formatter is configured (no ruff, black, flake8, isort, pre-commit).

## Project Structure

```
src/adif_manage/          # Main package (src layout)
  __init__.py             # Version
  __main__.py             # Entry point: main()
  cli.py                  # CLI loop (run_cli, run_app)
  commands.py             # Command parsing & validation
  record_flow.py          # Interactive QSO record entry
  adif_codec.py           # ADIF parse/serialize (pure functions)
  storage.py              # File I/O (read/write ADIF files)
  models.py               # Dataclasses (QSORecord, SessionState)
  errors.py               # Domain exceptions
tests/                    # Unit & integration tests
  __init__.py             # Adds src/ to sys.path
pyproject.toml            # Build config, coverage, mypy, pyright
pyrightconfig.json        # pyright include/extraPaths
flake.nix                 # Nix build
```

## Code Style

### Imports
- **Always** start modules with `from __future__ import annotations`
- Group: stdlib → third-party → relative locals (blank line between groups)
- Use explicit relative imports within package: `from .models import QSORecord`

```python
from __future__ import annotations
import sys
from collections.abc import Callable

from prompt_toolkit import PromptSession

from . import __version__
from .commands import BASE_COMMANDS
```

### Naming
- **Modules/files**: `snake_case` (`adif_codec.py`, `record_flow.py`)
- **Functions**: `snake_case` (`run_cli`, `parse_command_line`)
- **Variables**: `lower_snake` (`file_path`, `created_directory`)
- **Classes/dataclasses**: `PascalCase` (`QSORecord`, `SessionState`)
- **Constants**: `UPPER_SNAKE` (`CORE_REQUIRED_FIELDS`, `ALL_QSO_FIELDS`)
- **Private helpers**: `_prefix` (`_make_prompt_session`, `_field_label`)

### Types
- Use built-in generics: `list[str]`, `dict[str, str]` (not `List`, `Dict`)
- Use PEP 604 unions: `str | None` (not `Optional[str]`)
- Annotate all public function signatures and dataclass fields

```python
@dataclass(frozen=True)
class ParsedCommand:
    name: str
    argument: str | None
```

### Dataclasses
- Use `@dataclass` for domain objects and result types
- Use `frozen=True` for immutable command/value objects
- Use `field(default_factory=...)` for mutable defaults

### Error Handling
- Domain exceptions live in `errors.py` — inherit from `AdifManageError`
- Wrap low-level exceptions with `raise DomainError(...) from exc`
- CLI catches domain exceptions and writes user-facing messages to stderr
- Validation helpers return error lists (`list[str]`), not exceptions

```python
# errors.py
class AdifManageError(Exception): pass
class AdifParseError(AdifManageError): pass
class CommandError(AdifManageError): pass
class WriteError(AdifManageError): pass

# storage.py — wrap OSError
try:
    content = file_path.read_text(encoding="utf-8")
except OSError as exc:
    raise WriteError(f"读取文件失败: {exc}") from exc
```

### File I/O
- Use `pathlib.Path` (not `os.path`)
- Always specify `encoding="utf-8"`
- Use `"x"` mode for create-only, `"w"` for overwrite
- Return outcome dataclasses for multi-faceted results

### Formatting
- 4-space indentation
- f-strings for formatted messages
- Two blank lines between top-level definitions
- Double quotes for strings (observed convention)

## Testing Patterns

- Tests use `unittest.TestCase`; pytest runs them
- Inject I/O via callables to isolate user interaction (see `test_integration_cli.py`)
- Tests import via `src.adif_manage.*` (tests/__init__.py adds `src/` to path)
- File under `tests/test_<module>.py`

## Architecture

- **cli.py**: Top-level CLI loop, coordinates all modules
- **commands.py**: Parse/validate CLI commands (returns `ParsedCommand`)
- **record_flow.py**: Interactive data entry with validation
- **adif_codec.py**: Pure ADIF parse/serialize functions
- **storage.py**: Filesystem operations, wraps errors
- **models.py**: Data carriers and normalization
- **errors.py**: Exception hierarchy

Separation principle: parsing returns values or raises domain errors; validation returns error lists; storage translates OSErrors into `WriteError`.

## Language Notes

- User-facing messages are in **Chinese** (e.g., "当前没有 QSO 条目", "命令输入错误")
- Field names and ADIF identifiers are in **English** (e.g., QSO_DATE, CALL, MODE)
