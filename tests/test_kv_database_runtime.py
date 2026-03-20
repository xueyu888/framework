from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from kv_database_runtime.store import MemoryKvDatabase, MemoryKvDatabaseConfig, WalRecord, WriteAheadLog


def build_config(
    temp_dir: Path,
    *,
    allowed_operations: tuple[str, ...] = ("put", "get", "delete"),
    key_python_type: str = "str",
    missing_key_policy: str = "raise_key_error",
    value_serialization: str = "repr",
    line_delimiter: str = "\n",
) -> MemoryKvDatabaseConfig:
    return MemoryKvDatabaseConfig(
        allowed_operations=allowed_operations,
        read_operation="get",
        write_operations=("put", "delete"),
        missing_key_policy=missing_key_policy,
        key_python_type=key_python_type,
        value_python_type="Any",
        value_serialization=value_serialization,
        wal_directory=temp_dir,
        wal_filename="wal.log",
        create_parent_on_boot=True,
        record_format="json_lines",
        field_order=("operation", "key", "value_repr"),
        line_delimiter=line_delimiter,
        replay_strategy="append_only_replay",
    )


class WriteAheadLogTest(unittest.TestCase):
    def test_append_and_read_records_round_trip_with_repr_serialization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            wal = WriteAheadLog(config)
            expected = [
                WalRecord(operation="put", key="user", value={"name": "alice", "roles": ["admin"]}),
                WalRecord(operation="delete", key="user", value={"name": "alice", "roles": ["admin"]}),
            ]

            for record in expected:
                wal.append(record)

            self.assertEqual(wal.read_records(), expected)

    def test_read_records_skips_blank_lines_and_supports_json_serialization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir), value_serialization="json")
            wal = WriteAheadLog(config)
            wal.append(WalRecord(operation="put", key="doc", value={"title": "规范", "tags": ["kv", "wal"]}))
            config.wal_path.write_text(
                config.wal_path.read_text(encoding="utf-8") + "\n\n",
                encoding="utf-8",
            )

            records = wal.read_records()

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].operation, "put")
            self.assertEqual(records[0].key, "doc")
            self.assertEqual(records[0].value, {"title": "规范", "tags": ["kv", "wal"]})

    def test_read_records_returns_empty_list_when_wal_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            wal = WriteAheadLog(config)

            self.assertEqual(wal.read_records(), [])

    def test_unsupported_value_serialization_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir), value_serialization="yaml")
            wal = WriteAheadLog(config)

            with self.assertRaisesRegex(ValueError, "unsupported value serialization"):
                wal.append(WalRecord(operation="put", key="x", value=1))


class MemoryKvDatabaseTest(unittest.TestCase):
    def test_put_get_delete_and_snapshot_follow_expected_state_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = MemoryKvDatabase(build_config(Path(temp_dir)))

            database.put("alpha", {"count": 1})
            database.put("beta", 2)

            self.assertEqual(database.get("alpha"), {"count": 1})
            self.assertEqual(database.snapshot(), {"alpha": {"count": 1}, "beta": 2})

            deleted = database.delete("alpha")

            self.assertEqual(deleted, {"count": 1})
            self.assertEqual(database.snapshot(), {"beta": 2})

    def test_missing_key_operations_raise_key_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = MemoryKvDatabase(build_config(Path(temp_dir)))

            with self.assertRaises(KeyError):
                database.get("missing")

            with self.assertRaises(KeyError):
                database.delete("missing")

    def test_from_config_recovers_state_from_existing_wal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            first_database = MemoryKvDatabase(config)
            first_database.put("alpha", 1)
            first_database.put("beta", {"nested": True})
            first_database.delete("alpha")

            recovered = MemoryKvDatabase.from_config(config)

            self.assertEqual(recovered.snapshot(), {"beta": {"nested": True}})
            self.assertEqual(recovered.get("beta"), {"nested": True})

    def test_delete_disallowed_by_config_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir), allowed_operations=("put", "get"))
            database = MemoryKvDatabase(config)
            database.put("alpha", 1)

            with self.assertRaisesRegex(ValueError, "unsupported operation: delete"):
                database.delete("alpha")

    def test_invalid_key_contract_and_non_string_keys_raise(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            contract_database = MemoryKvDatabase(build_config(Path(temp_dir), key_python_type="int"))

            with self.assertRaisesRegex(ValueError, "unsupported key type contract"):
                contract_database.put("alpha", 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            database = MemoryKvDatabase(build_config(Path(temp_dir)))

            with self.assertRaises(TypeError):
                database.put(1, "value")  # type: ignore[arg-type]

    def test_recover_rejects_unknown_wal_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.wal_path.write_text(
                '{"key": "alpha", "operation": "rename", "value_repr": "1"}\n',
                encoding="utf-8",
            )
            database = MemoryKvDatabase(config)

            with self.assertRaisesRegex(ValueError, "unsupported WAL operation during recovery"):
                database.recover()


if __name__ == "__main__":
    unittest.main()
