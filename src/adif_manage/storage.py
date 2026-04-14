from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adif_codec import parse_adi, to_adi
from .errors import AdifParseError, WriteError
from .models import QSORecord


@dataclass
class WriteOutcome:
    created_directory: bool
    overwritten_file: bool


def read_records(path: str) -> list[QSORecord]:
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteError(f"读取文件失败: {exc}") from exc

    try:
        return parse_adi(content)
    except AdifParseError as exc:
        raise WriteError(f"解析 ADI 内容失败: {exc}") from exc


def write_records(
    path: str,
    records: list[QSORecord],
    adif_version: str,
    program_version: str,
    overwrite: bool,
    create_parents: bool,
) -> WriteOutcome:
    file_path = Path(path)
    parent = file_path.parent if str(file_path.parent) else Path(".")

    created_directory = False
    overwritten_file = False

    if not parent.exists():
        if create_parents:
            try:
                parent.mkdir(parents=True, exist_ok=True)
                created_directory = True
            except OSError as exc:
                raise WriteError(f"创建目录失败: {exc}") from exc
        else:
            raise WriteError("写入失败: 目录不存在")

    if file_path.exists():
        if overwrite:
            overwritten_file = True
        else:
            raise WriteError("写入失败: 文件已存在")

    content = to_adi(records=records, adif_version=adif_version, program_version=program_version)

    mode = "w" if overwrite else "x"
    try:
        with file_path.open(mode, encoding="utf-8") as fp:
            fp.write(content)
    except OSError as exc:
        raise WriteError(f"写入失败: {exc}") from exc

    return WriteOutcome(created_directory=created_directory, overwritten_file=overwritten_file)
