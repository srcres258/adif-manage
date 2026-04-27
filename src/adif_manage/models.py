from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QSORecord:
    fields: dict[str, str] = field(default_factory=dict)

    def normalized(self) -> "QSORecord":
        normalized_fields: dict[str, str] = {}
        for key, value in self.fields.items():
            key_norm = key.strip().upper()
            value_norm = value.strip()
            if key_norm and value_norm:
                normalized_fields[key_norm] = value_norm
        return QSORecord(fields=normalized_fields)


@dataclass
class SessionState:
    records: list[QSORecord] = field(default_factory=list)
    dirty: bool = False
    last_write_path: str | None = None
    last_record_fields: dict[str, str] = field(default_factory=dict)
