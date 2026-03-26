from __future__ import annotations

import random
import unittest
from typing import Any, ClassVar, Mapping, Protocol, cast

from project_runtime.code_layer import CodeModuleBinding, build_code_modules
from project_runtime.compiler import _read_root_role_dependencies
from project_runtime.config_layer import build_config_modules, load_project_config
from project_runtime.correspondence_contracts import BaseContract, RuleContract
from project_runtime.framework_layer import resolve_selected_framework_modules


PROJECT_FILE = "projects/zz_chunk_tagging_basic/project.toml"
RANDOMIZED_TEST_SEED = 20260325
EXPECTED_MODULE_IDS = (
    "Chunk_Tagging.L0.M0",
    "Chunk_Tagging.L1.M0",
    "Chunk_Tagging.L1.M1",
    "Chunk_Tagging.L1.M2",
    "Chunk_Tagging.L2.M0",
    "Chunk_Tagging.L2.M1",
    "Chunk_Tagging.L2.M2",
    "Chunk_Tagging.L3.M0",
)


class ChunkTaggingModuleInstanceProtocol(Protocol):
    static_params: Any
    boundary_context: dict[str, dict[str, Any]]

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        ...


class ChunkTaggingModuleTypeProtocol(Protocol):
    boundary_field_map: ClassVar[dict[str, str]]
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]]
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]]

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingModuleInstanceProtocol:
        ...


def _load_chunk_tagging_code_bindings() -> tuple[CodeModuleBinding, ...]:
    project_config = load_project_config(PROJECT_FILE)
    framework_modules, root_module_ids = resolve_selected_framework_modules(project_config.framework_modules)
    config_modules = build_config_modules(project_config, framework_modules)
    code_modules, _ = build_code_modules(
        config_modules,
        root_module_ids=root_module_ids,
        root_role_dependencies=_read_root_role_dependencies(project_config.exact),
    )
    return code_modules


def _module_static_payload(binding: CodeModuleBinding) -> dict[str, Any]:
    modules = binding.code_module.exact_export.get("modules")
    if not isinstance(modules, dict):
        raise AssertionError(f"missing exact_export.modules for {binding.framework_module.module_id}")
    module_payload = modules.get(binding.code_module.module_key)
    if not isinstance(module_payload, dict):
        raise AssertionError(f"missing exact_export.modules.{binding.code_module.module_key}")
    static_params = module_payload.get("static_params")
    if not isinstance(static_params, dict):
        raise AssertionError(f"missing static_params for {binding.framework_module.module_id}")
    return dict(static_params)


def _random_boundary_payload(
    rng: random.Random,
    *,
    module_id: str,
    field_name: str,
    flavor: str,
    iteration: int,
) -> dict[str, object]:
    rank = rng.randrange(10_000)
    return {
        "token": f"{module_id}:{field_name}:{flavor}:{iteration}:{rank}",
        "enabled": bool(rng.randrange(2)),
        "rank": rank,
        "labels": [f"label_{rng.randrange(8)}", f"label_{rng.randrange(8)}"],
        "meta": {
            "bucket": f"bucket_{rng.randrange(5)}",
            "weight": round(rng.random(), 4),
        },
    }


class ChunkTaggingModuleContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.code_bindings = _load_chunk_tagging_code_bindings()
        cls.binding_by_module_id = {
            binding.framework_module.module_id: binding
            for binding in cls.code_bindings
        }

    def test_chunk_tagging_code_bindings_cover_every_module(self) -> None:
        self.assertEqual(
            tuple(binding.framework_module.module_id for binding in self.code_bindings),
            EXPECTED_MODULE_IDS,
        )

    def test_each_module_instantiates_declared_bases_rules_and_boundaries(self) -> None:
        for module_id, binding in self.binding_by_module_id.items():
            with self.subTest(module_id=module_id):
                module_type = cast(
                    type[ChunkTaggingModuleTypeProtocol],
                    binding.code_module.ModuleType,
                )
                static_payload = _module_static_payload(binding)
                module_instance = module_type.from_payload(static_payload)

                self.assertEqual(module_instance.static_params.to_dict(), static_payload)
                self.assertEqual(
                    set(module_instance.boundary_context),
                    set(module_type.boundary_field_map),
                )

                expected_base_ids = tuple(
                    item["base_id"]
                    for item in binding.code_module.code_bindings["base_class_bindings"]
                )
                expected_rule_ids = tuple(
                    item["rule_id"]
                    for item in binding.code_module.code_bindings["rule_class_bindings"]
                )

                self.assertEqual(
                    tuple(base_type.framework_base_id for base_type in module_type.BaseTypes),
                    expected_base_ids,
                )
                self.assertEqual(
                    tuple(rule_type.framework_rule_id for rule_type in module_type.RuleTypes),
                    expected_rule_ids,
                )

                for boundary_id, field_name in module_type.boundary_field_map.items():
                    expected_value = static_payload[field_name]
                    self.assertEqual(module_instance.boundary_value(boundary_id), expected_value)
                    boundary_context = module_instance.boundary_context[boundary_id]
                    self.assertEqual(boundary_context["static_value"], expected_value)
                    self.assertEqual(boundary_context["runtime_value"], "UNSET")
                    self.assertFalse(boundary_context["runtime_provided"])
                    self.assertEqual(boundary_context["value"], expected_value)

                for base_type in module_type.BaseTypes:
                    attr_name = base_type.framework_base_short_id.lower()
                    base_instance = getattr(module_instance, attr_name)
                    self.assertIsInstance(base_instance, base_type)
                    for boundary_id in base_type.boundary_ids:
                        self.assertEqual(
                            base_instance.boundary_value(boundary_id),
                            module_instance.boundary_value(boundary_id),
                        )

                for rule_type in module_type.RuleTypes:
                    attr_name = rule_type.framework_rule_short_id.lower()
                    rule_instance = getattr(module_instance, attr_name)
                    self.assertIsInstance(rule_instance, rule_type)

    def test_randomized_runtime_overrides_win_for_every_module(self) -> None:
        rng = random.Random(RANDOMIZED_TEST_SEED)
        for module_id, binding in self.binding_by_module_id.items():
            module_type = cast(
                type[ChunkTaggingModuleTypeProtocol],
                binding.code_module.ModuleType,
            )
            field_names = tuple(module_type.boundary_field_map.values())
            for iteration in range(8):
                with self.subTest(module_id=module_id, iteration=iteration):
                    static_payload = {
                        field_name: _random_boundary_payload(
                            rng,
                            module_id=module_id,
                            field_name=field_name,
                            flavor="static",
                            iteration=iteration,
                        )
                        for field_name in field_names
                    }
                    runtime_payload: dict[str, Any] = {}
                    for field_name in field_names:
                        if rng.randrange(2):
                            runtime_payload[field_name] = _random_boundary_payload(
                                rng,
                                module_id=module_id,
                                field_name=field_name,
                                flavor="runtime",
                                iteration=iteration,
                            )
                    if not runtime_payload:
                        first_field = field_names[0]
                        runtime_payload[first_field] = _random_boundary_payload(
                            rng,
                            module_id=module_id,
                            field_name=first_field,
                            flavor="runtime",
                            iteration=iteration,
                        )

                    module_instance = module_type.from_payload(static_payload, runtime_payload)

                    for boundary_id, field_name in module_type.boundary_field_map.items():
                        boundary_context = module_instance.boundary_context[boundary_id]
                        expected_static = static_payload[field_name]
                        expected_value = runtime_payload.get(field_name, expected_static)

                        self.assertEqual(boundary_context["static_value"], expected_static)
                        self.assertEqual(boundary_context["value"], expected_value)
                        self.assertEqual(module_instance.boundary_value(boundary_id), expected_value)

                        if field_name in runtime_payload:
                            self.assertTrue(boundary_context["runtime_provided"])
                            self.assertEqual(
                                boundary_context["runtime_value"],
                                runtime_payload[field_name],
                            )
                        else:
                            self.assertFalse(boundary_context["runtime_provided"])
                            self.assertEqual(boundary_context["runtime_value"], "UNSET")

    def test_randomized_invalid_boundary_values_raise_value_error(self) -> None:
        rng = random.Random(RANDOMIZED_TEST_SEED + 1)
        invalid_values: tuple[object, ...] = (None, 7, "invalid", ["not", "a", "dict"])

        for module_id, binding in self.binding_by_module_id.items():
            module_type = cast(
                type[ChunkTaggingModuleTypeProtocol],
                binding.code_module.ModuleType,
            )
            field_map_items = tuple(module_type.boundary_field_map.items())
            for iteration in range(4):
                with self.subTest(module_id=module_id, iteration=iteration):
                    static_payload: dict[str, Any] = {
                        field_name: _random_boundary_payload(
                            rng,
                            module_id=module_id,
                            field_name=field_name,
                            flavor="static",
                            iteration=iteration,
                        )
                        for _, field_name in field_map_items
                    }
                    boundary_id, field_name = rng.choice(field_map_items)
                    static_payload[field_name] = rng.choice(invalid_values)

                    module_instance = module_type.from_payload(static_payload)

                    with self.assertRaisesRegex(ValueError, "module boundary value must be a dict"):
                        module_instance.boundary_value(boundary_id)


if __name__ == "__main__":
    unittest.main()
