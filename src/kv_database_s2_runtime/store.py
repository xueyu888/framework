from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WalRecord:
    operation: str
    key: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "key": self.key,
            "value": self.value,
        }


@dataclass(frozen=True)
class MemoryKvDatabaseS2Config:
    max_items: int
    overflow_policy: str
    allowed_operations: tuple[str, ...]
    read_operation: str
    write_operations: tuple[str, ...]
    missing_key_policy: str
    key_python_type: str
    value_python_type: str
    value_serialization: str
    wal_directory: Path
    wal_filename: str
    create_parent_on_boot: bool
    record_format: str
    field_order: tuple[str, ...]
    line_delimiter: str
    replay_strategy: str
    snapshot_directory: Path
    snapshot_filename: str
    snapshot_create_parent_on_boot: bool
    snapshot_record_format: str
    snapshot_line_delimiter: str
    compact_wal_on_checkpoint: bool
    checkpoint_trigger: str
    checkpoint_every_write_operations: int
    recovery_strategy: str

    @property
    def wal_path(self) -> Path:
        return self.wal_directory / self.wal_filename

    @property
    def snapshot_path(self) -> Path:
        return self.snapshot_directory / self.snapshot_filename


def _encode_value(serialization: str, value: Any) -> str:
    if serialization == "repr":
        return repr(value)
    if serialization == "json":
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    raise ValueError(f"unsupported value serialization: {serialization}")


def _decode_value(serialization: str, payload: str) -> Any:
    if serialization == "repr":
        try:
            return ast.literal_eval(payload)
        except (SyntaxError, ValueError):
            return payload
    if serialization == "json":
        return json.loads(payload)
    raise ValueError(f"unsupported value serialization: {serialization}")


class WriteAheadLog:
    def __init__(self, config: MemoryKvDatabaseS2Config) -> None:
        self._config = config
        if config.create_parent_on_boot:
            config.wal_directory.mkdir(parents=True, exist_ok=True)

    def append(self, record: WalRecord) -> None:
        payload = {
            "operation": record.operation,
            "key": record.key,
            "value_repr": _encode_value(self._config.value_serialization, record.value),
        }
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + self._config.line_delimiter
        with self._config.wal_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def read_records(self) -> list[WalRecord]:
        if not self._config.wal_path.exists():
            return []
        records: list[WalRecord] = []
        with self._config.wal_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                text = raw_line.strip()
                if not text:
                    continue
                payload = json.loads(text)
                records.append(
                    WalRecord(
                        operation=str(payload["operation"]),
                        key=str(payload["key"]),
                        value=_decode_value(
                            self._config.value_serialization,
                            str(payload.get("value_repr", "None")),
                        ),
                    )
                )
        return records

    def reset(self) -> None:
        if self._config.create_parent_on_boot:
            self._config.wal_directory.mkdir(parents=True, exist_ok=True)
        self._config.wal_path.write_text("", encoding="utf-8")


class SnapshotStore:
    def __init__(self, config: MemoryKvDatabaseS2Config) -> None:
        self._config = config
        if config.snapshot_create_parent_on_boot:
            config.snapshot_directory.mkdir(parents=True, exist_ok=True)

    def write_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        if self._config.snapshot_create_parent_on_boot:
            self._config.snapshot_directory.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(
                {key: _encode_value(self._config.value_serialization, value)},
                ensure_ascii=False,
                sort_keys=True,
            )
            for key, value in sorted(state.items())
        ]
        text = self._config.snapshot_line_delimiter.join(lines)
        if lines:
            text += self._config.snapshot_line_delimiter
        self._config.snapshot_path.write_text(text, encoding="utf-8")
        return dict(state)

    def read_snapshot(self) -> dict[str, Any]:
        if not self._config.snapshot_path.exists():
            return {}
        recovered: dict[str, Any] = {}
        with self._config.snapshot_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                text = raw_line.strip()
                if not text:
                    continue
                payload = json.loads(text)
                if not isinstance(payload, dict) or len(payload) != 1:
                    raise ValueError("snapshot lines must each contain exactly one key/value pair")
                key, encoded_value = next(iter(payload.items()))
                recovered[str(key)] = _decode_value(self._config.value_serialization, str(encoded_value))
        return recovered


class MemoryKvDatabaseS2:
    def __init__(
        self,
        config: MemoryKvDatabaseS2Config,
        wal: WriteAheadLog | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self._config = config
        self._wal = wal or WriteAheadLog(config)
        self._snapshot_store = snapshot_store or SnapshotStore(config)
        self._store: dict[str, Any] = {}
        self._writes_since_checkpoint = 0

    @classmethod
    def from_config(cls, config: MemoryKvDatabaseS2Config) -> "MemoryKvDatabaseS2":
        database = cls(config=config)
        database.recover()
        return database

    def put(self, key: str, value: Any) -> None:
        self._assert_operation_allowed("put")
        self._assert_key(key)
        self._assert_capacity(key)
        self._wal.append(WalRecord(operation="put", key=key, value=value))
        self._store[key] = value
        self._after_write()

    def get(self, key: str) -> Any:
        self._assert_operation_allowed(self._config.read_operation)
        self._assert_key(key)
        if key not in self._store:
            self._raise_missing_key(key)
        return self._store[key]

    def delete(self, key: str) -> Any:
        self._assert_operation_allowed("delete")
        self._assert_key(key)
        if key not in self._store:
            self._raise_missing_key(key)
        value = self._store[key]
        self._wal.append(WalRecord(operation="delete", key=key, value=value))
        del self._store[key]
        self._after_write()
        return value

    def recover(self) -> dict[str, Any]:
        if self._config.recovery_strategy != "snapshot_then_wal_replay":
            raise ValueError(f"unsupported recovery strategy: {self._config.recovery_strategy}")
        recovered = self._snapshot_store.read_snapshot()
        for record in self._wal.read_records():
            if record.operation == "put":
                recovered[record.key] = record.value
            elif record.operation == "delete":
                recovered.pop(record.key, None)
            else:
                raise ValueError(f"unsupported WAL operation during recovery: {record.operation}")
        self._store = recovered
        self._writes_since_checkpoint = 0
        return dict(self._store)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._store)

    def checkpoint(self) -> dict[str, Any]:
        snapshot = self._snapshot_store.write_snapshot(self._store)
        if self._config.compact_wal_on_checkpoint:
            self._wal.reset()
        self._writes_since_checkpoint = 0
        return snapshot

    def _after_write(self) -> None:
        self._writes_since_checkpoint += 1
        if self._config.checkpoint_trigger != "every_n_writes":
            raise ValueError(f"unsupported checkpoint trigger: {self._config.checkpoint_trigger}")
        threshold = self._config.checkpoint_every_write_operations
        if threshold > 0 and self._writes_since_checkpoint >= threshold:
            self.checkpoint()

    def _assert_operation_allowed(self, operation: str) -> None:
        if operation not in self._config.allowed_operations:
            raise ValueError(f"unsupported operation: {operation}")

    def _assert_key(self, key: str) -> None:
        if self._config.key_python_type != "str":
            raise ValueError(f"unsupported key type contract: {self._config.key_python_type}")
        if not isinstance(key, str):
            raise TypeError("KV database keys must be str")

    def _assert_capacity(self, key: str) -> None:
        if key in self._store:
            return
        if len(self._store) < self._config.max_items:
            return
        if self._config.overflow_policy == "raise_limit_error":
            raise ValueError("kv database item limit reached")
        raise ValueError(f"unsupported overflow policy: {self._config.overflow_policy}")

    def _raise_missing_key(self, key: str) -> None:
        if self._config.missing_key_policy == "raise_key_error":
            raise KeyError(key)
        raise ValueError(f"unsupported missing key policy: {self._config.missing_key_policy}")
