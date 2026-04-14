from __future__ import annotations

import re
from datetime import datetime

from .errors import AdifParseError
from .models import QSORecord

CORE_REQUIRED_FIELDS = ("QSO_DATE", "TIME_ON", "CALL", "MODE")
CORE_FREQ_OR_BAND = ("FREQ", "BAND")

FIELD_TOKEN_PATTERN = re.compile(r"^([A-Za-z0-9_]+):(\d+)(?::([A-Za-z]))?$")
DATE_PATTERN = re.compile(r"^\d{8}$")
TIME_PATTERN = re.compile(r"^\d{4}(\d{2})?$")


def missing_required_fields(fields: dict[str, str]) -> list[str]:
    normalized = {key.upper(): value for key, value in fields.items() if value.strip()}
    missing: list[str] = []

    for field in CORE_REQUIRED_FIELDS:
        if field not in normalized:
            missing.append(field)

    if "FREQ" not in normalized and "BAND" not in normalized:
        missing.append("FREQ/BAND")

    return missing


def validate_core_field_formats(fields: dict[str, str]) -> list[str]:
    errors: list[str] = []
    qso_date = fields.get("QSO_DATE", "")
    time_on = fields.get("TIME_ON", "")

    if qso_date:
        if not DATE_PATTERN.match(qso_date):
            errors.append("QSO_DATE")
        else:
            try:
                datetime.strptime(qso_date, "%Y%m%d")
            except ValueError:
                errors.append("QSO_DATE")

    if time_on:
        if not TIME_PATTERN.match(time_on):
            errors.append("TIME_ON")
        else:
            if len(time_on) == 4:
                hh = int(time_on[0:2])
                mm = int(time_on[2:4])
                if hh > 23 or mm > 59:
                    errors.append("TIME_ON")
            else:
                hh = int(time_on[0:2])
                mm = int(time_on[2:4])
                ss = int(time_on[4:6])
                if hh > 23 or mm > 59 or ss > 59:
                    errors.append("TIME_ON")

    return errors


def parse_adi(content: str) -> list[QSORecord]:
    records: list[QSORecord] = []
    current: dict[str, str] = {}
    index = 0

    while index < len(content):
        tag_start = content.find("<", index)
        if tag_start == -1:
            break

        tag_end = content.find(">", tag_start + 1)
        if tag_end == -1:
            raise AdifParseError("Malformed ADI tag: missing '>'")

        token = content[tag_start + 1 : tag_end].strip()
        token_upper = token.upper()
        index = tag_end + 1

        if token_upper == "EOH":
            continue

        if token_upper == "EOR":
            if current:
                records.append(QSORecord(fields=current).normalized())
                current = {}
            continue

        match = FIELD_TOKEN_PATTERN.match(token)
        if not match:
            raise AdifParseError(f"Malformed ADI field token: <{token}>")

        field_name = match.group(1).upper()
        value_length = int(match.group(2))

        value_end = index + value_length
        if value_end > len(content):
            raise AdifParseError(f"Invalid length for field {field_name}")

        value = content[index:value_end]
        index = value_end
        current[field_name] = value

    if current:
        records.append(QSORecord(fields=current).normalized())

    return records


def _ordered_field_names(fields: dict[str, str]) -> list[str]:
    names = [name for name, value in fields.items() if value.strip()]
    required_present = [name for name in (*CORE_REQUIRED_FIELDS, *CORE_FREQ_OR_BAND) if name in names]
    remaining = sorted(name for name in names if name not in required_present)
    return required_present + remaining


def to_adi(records: list[QSORecord], adif_version: str, program_version: str) -> str:
    output_parts = [
        f"<ADIF_VER:{len(adif_version)}>{adif_version}",
        "<PROGRAMID:11>adif-manage",
        f"<PROGRAMVERSION:{len(program_version)}>{program_version}",
        "<EOH>",
    ]

    for record in records:
        fields = record.normalized().fields
        for field_name in _ordered_field_names(fields):
            value = fields[field_name]
            output_parts.append(f"<{field_name}:{len(value)}>{value}")
        output_parts.append("<EOR>")

    return "\n".join(output_parts) + "\n"
