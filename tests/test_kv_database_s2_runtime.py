from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from project_runtime.compiler import compile_project_runtime
from kv_database_s2_runtime.store import (
    MemoryKvDatabaseS2,
    MemoryKvDatabaseS2Config,
    SnapshotStore,
    WalRecord,
    WriteAheadLog,
)


def build_config(
    temp_dir: Path,
    *,
    checkpoint_every_write_operations: int = 2,
    max_items: int = 100,
) -> MemoryKvDatabaseS2Config:
    return MemoryKvDatabaseS2Config(
        max_items=max_items,
        overflow_policy="raise_limit_error",
        allowed_operations=("put", "get", "delete"),
        read_operation="get",
        write_operations=("put", "delete"),
        missing_key_policy="raise_key_error",
        key_python_type="str",
        value_python_type="Any",
        value_serialization="repr",
        wal_directory=temp_dir,
        wal_filename="wal.log",
        create_parent_on_boot=True,
        record_format="json_lines",
        field_order=("operation", "key", "value_repr"),
        line_delimiter="\n",
        replay_strategy="snapshot_then_wal_replay",
        snapshot_directory=temp_dir,
        snapshot_filename="checkpoint.snapshot",
        snapshot_create_parent_on_boot=True,
        snapshot_record_format="json_lines_key_value_map",
        snapshot_line_delimiter="\n",
        compact_wal_on_checkpoint=True,
        checkpoint_trigger="every_n_writes",
        checkpoint_every_write_operations=checkpoint_every_write_operations,
        recovery_strategy="snapshot_then_wal_replay",
    )


class SnapshotStoreTest(unittest.TestCase):
    def test_snapshot_round_trip_preserves_current_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            snapshot_store = SnapshotStore(config)
            expected = {"alpha": {"count": 1}, "beta": [1, 2, 3]}

            snapshot_store.write_snapshot(expected)

            self.assertEqual(snapshot_store.read_snapshot(), expected)


class MemoryKvDatabaseS2Test(unittest.TestCase):
    def test_checkpoint_writes_snapshot_and_compacts_wal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir), checkpoint_every_write_operations=2)
            database = MemoryKvDatabaseS2(config)

            database.put("alpha", 1)
            database.put("beta", 2)

            self.assertEqual(database.snapshot(), {"alpha": 1, "beta": 2})
            self.assertEqual(config.wal_path.read_text(encoding="utf-8"), "")
            snapshot_text = config.snapshot_path.read_text(encoding="utf-8")
            self.assertIn('"alpha"', snapshot_text)
            self.assertIn('"beta"', snapshot_text)

    def test_recover_uses_snapshot_then_remaining_wal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir), checkpoint_every_write_operations=10)
            database = MemoryKvDatabaseS2(config)
            database.put("alpha", 1)
            database.put("beta", 2)
            database.checkpoint()
            database.put("beta", 3)
            database.put("gamma", {"nested": True})

            recovered = MemoryKvDatabaseS2.from_config(config)

            self.assertEqual(
                recovered.snapshot(),
                {"alpha": 1, "beta": 3, "gamma": {"nested": True}},
            )

    def test_capacity_limit_rejects_new_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = MemoryKvDatabaseS2(build_config(Path(temp_dir), max_items=1))
            database.put("alpha", 1)

            with self.assertRaisesRegex(ValueError, "item limit reached"):
                database.put("beta", 2)

    def test_project_runtime_compiles_kv_database_s2_spec(self) -> None:
        assembly = compile_project_runtime("projects/kv_database_s2/project.toml")

        spec = assembly.require_runtime_export("kv_database_runtime_spec")
        self.assertEqual(spec["contract"]["count"]["max_items"], 10000)
        self.assertEqual(spec["contract"]["recover"]["strategy"], "snapshot_then_wal_replay")
        self.assertEqual(spec["runtime"]["implementation"]["database_class"], "kv_database_s2_runtime.store:MemoryKvDatabaseS2")
        self.assertEqual(spec["snapshot"]["filename"], "checkpoint.snapshot")
        self.assertTrue(assembly.validation_reports.passed)


if __name__ == "__main__":
    unittest.main()
