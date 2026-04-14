from __future__ import annotations

from dataclasses import dataclass

from .errors import CommandError

BASE_COMMANDS = (
    "help",
    "list",
    "record",
    "read",
    "write",
    "write-force",
    "delete",
    "quit",
    "quit-force",
)

ALIASES: dict[str, str] = {
    "h": "help",
    "ls": "list",
    "rec": "record",
    "r": "read",
    "w": "write",
    "wf": "write-force",
    "d": "delete",
    "q": "quit",
    "qf": "quit-force",
}


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    argument: str | None


@dataclass(frozen=True)
class DeleteTarget:
    start: int
    end: int


def command_names() -> tuple[str, ...]:
    return BASE_COMMANDS + tuple(ALIASES.keys())


def parse_command_line(line: str) -> ParsedCommand:
    stripped = line.strip()
    if not stripped:
        raise CommandError("命令输入错误。用 help 命令查看所有命令")

    parts = stripped.split(maxsplit=1)
    raw_name = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else None

    command_name = ALIASES.get(raw_name, raw_name)
    if command_name not in BASE_COMMANDS:
        raise CommandError("命令输入错误。用 help 命令查看所有命令")

    if command_name in {"read", "write", "write-force"}:
        if argument is not None:
            argument = line.strip()[len(parts[0]) :].lstrip()

    return ParsedCommand(name=command_name, argument=argument)


def parse_delete_target(argument: str | None, length: int) -> DeleteTarget:
    if not argument:
        raise CommandError("delete 命令缺少参数")

    token = argument.strip()
    if "-" in token:
        sub = token.split("-")
        if len(sub) != 2 or not sub[0].isdigit() or not sub[1].isdigit():
            raise CommandError("delete 参数格式错误")
        start = int(sub[0])
        end = int(sub[1])
    else:
        if not token.isdigit():
            raise CommandError("delete 参数格式错误")
        start = int(token)
        end = start

    if start < 1 or end < 1 or start > end or end > length:
        raise CommandError("delete 序号超出范围")

    return DeleteTarget(start=start, end=end)
