from __future__ import annotations

import sys

from .cli import run_app


def main() -> int:
    startup_file = sys.argv[1] if len(sys.argv) > 1 else None
    return run_app(startup_file=startup_file)


if __name__ == "__main__":
    raise SystemExit(main())
