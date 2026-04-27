from __future__ import annotations

import sys
from collections.abc import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from . import __version__
from .commands import BASE_COMMANDS, command_names, parse_command_line, parse_delete_target
from .errors import CommandError, WriteError
from .models import QSORecord, SessionState
from .record_flow import run_record_interaction
from .storage import read_records, write_records

HELP_TEXT = """支持命令:
help
list
record
read <file>
write <file>
write-force <file>
delete <id> | delete <m-n>
quit
quit-force
"""


def _make_prompt_session() -> PromptSession[str]:
    completer = WordCompleter(command_names(), ignore_case=True)
    return PromptSession(completer=completer)


def _print_record(index: int, record: QSORecord, stdout_write: Callable[[str], None]) -> None:
    fields = record.normalized().fields
    stdout_write(f"{index}:\n")
    for key in sorted(fields):
        stdout_write(f"  {key}={fields[key]}\n")


def run_cli(
    state: SessionState,
    stdin_readline,
    stdout_write,
    stderr_write,
    prompt_func: Callable[[str], str] | None = None,
) -> int:
    while True:
        if prompt_func is not None:
            try:
                line = prompt_func("adif-manage> ")
            except KeyboardInterrupt:
                continue
            except EOFError:
                return 0
        else:
            stdout_write("adif-manage> ")
            line = stdin_readline()
            if line == "":
                return 0

        try:
            parsed = parse_command_line(line)
        except CommandError as exc:
            stderr_write(f"{exc}\n")
            continue

        name = parsed.name
        arg = parsed.argument

        if name == "help":
            stdout_write(HELP_TEXT)
            continue

        if name == "list":
            if not state.records:
                stdout_write("当前没有 QSO 条目\n")
                continue
            for idx, record in enumerate(state.records, start=1):
                _print_record(idx, record, stdout_write)
            continue

        if name == "record":
            result = run_record_interaction(
                stdin_readline=stdin_readline,
                stdout_write=stdout_write,
                last_fields=state.last_record_fields,
            )
            if result is not None:
                fields, snapshot = result
                state.records.append(QSORecord(fields=fields).normalized())
                state.last_record_fields = snapshot
                state.dirty = True
            continue

        if name == "read":
            if not arg:
                stderr_write("read 命令缺少文件路径\n")
                continue
            try:
                state.records = read_records(arg)
                state.dirty = False
            except WriteError as exc:
                stderr_write(f"{exc}\n")
            continue

        if name in {"write", "write-force"}:
            path = arg
            if path:
                state.last_write_path = path
            elif state.last_write_path:
                path = state.last_write_path
            else:
                stderr_write("write 命令缺少文件路径且无历史路径\n")
                continue

            try:
                outcome = write_records(
                    path=path,
                    records=state.records,
                    adif_version="3.1.7",
                    program_version=__version__,
                    overwrite=name == "write-force",
                    create_parents=name == "write-force",
                )
            except WriteError as exc:
                stderr_write(f"{exc}\n")
                continue

            if name == "write-force":
                if outcome.created_directory:
                    stdout_write("软件已递归自动创建目录\n")
                if outcome.overwritten_file:
                    stdout_write("软件已覆盖文件\n")
            state.dirty = False
            continue

        if name == "delete":
            try:
                target = parse_delete_target(arg, len(state.records))
            except CommandError as exc:
                stderr_write(f"{exc}\n")
                continue
            del state.records[target.start - 1 : target.end]
            state.dirty = True
            continue

        if name == "quit":
            if state.dirty:
                stdout_write("您还有未写入文件的 QSO，退出失败\n")
                continue
            return 0

        if name == "quit-force":
            return 0


def run_app(startup_file: str | None) -> int:
    state = SessionState()
    if startup_file:
        try:
            state.records = read_records(startup_file)
            state.dirty = False
        except WriteError as exc:
            sys.stderr.write(f"{exc}\n")
            return 1

    session = _make_prompt_session()
    return run_cli(
        state=state,
        stdin_readline=sys.stdin.readline,
        stdout_write=sys.stdout.write,
        stderr_write=sys.stderr.write,
        prompt_func=session.prompt,
    )
