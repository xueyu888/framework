from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from pkgutil import walk_packages
import re
from typing import Any

from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
)
from project_runtime.static_modules.common import StaticModuleContractBundle

_FRAMEWORK_MODULE_ID_PATTERN = re.compile(r"^[A-Za-z_]+\.[L]\d+\.[M]\d+$")


def _iter_candidate_module_names() -> list[str]:
    root_path = Path(__file__).resolve().parent
    names = {
        item.name
        for item in walk_packages([str(root_path)], prefix="project_runtime.static_modules.")
        if not item.ispkg
    }
    return sorted(names)


def _own_classes(module: Any) -> list[type[Any]]:
    return [
        item
        for item in vars(module).values()
        if inspect.isclass(item) and item.__module__ == module.__name__
    ]


def _extract_bundles(module_name: str) -> list[tuple[str, StaticModuleContractBundle]]:
    module = importlib.import_module(module_name)
    module_types = [
        item
        for item in _own_classes(module)
        if issubclass(item, ModuleContract) and item is not ModuleContract
    ]
    if not module_types:
        return []

    bundles: list[tuple[str, StaticModuleContractBundle]] = []
    for module_type in module_types:
        module_id = str(getattr(module_type, "framework_module_id", "")).strip()
        if not _FRAMEWORK_MODULE_ID_PATTERN.match(module_id):
            raise ValueError(f"invalid framework_module_id in {module_name}: {module_id}")

        static_params_type = getattr(module_type, "StaticBoundaryParams", None)
        runtime_params_type = getattr(module_type, "RuntimeBoundaryParams", None)
        base_types = tuple(getattr(module_type, "BaseTypes", tuple()))
        rule_types = tuple(getattr(module_type, "RuleTypes", tuple()))

        if not inspect.isclass(static_params_type) or not issubclass(static_params_type, StaticBoundaryParamsContract):
            raise TypeError(f"invalid StaticBoundaryParams in {module_name}:{module_type.__name__}")
        if not inspect.isclass(runtime_params_type) or not issubclass(runtime_params_type, RuntimeBoundaryParamsContract):
            raise TypeError(f"invalid RuntimeBoundaryParams in {module_name}:{module_type.__name__}")
        if not all(inspect.isclass(item) and issubclass(item, BaseContract) for item in base_types):
            raise TypeError(f"invalid BaseTypes in {module_name}:{module_type.__name__}")
        if not all(inspect.isclass(item) and issubclass(item, RuleContract) for item in rule_types):
            raise TypeError(f"invalid RuleTypes in {module_name}:{module_type.__name__}")

        bundles.append(
            (
                module_id,
                StaticModuleContractBundle(
                    module_type=module_type,
                    static_params_type=static_params_type,
                    runtime_params_type=runtime_params_type,
                    base_types=base_types,
                    rule_types=rule_types,
                ),
            )
        )
    return bundles


def _build_static_module_contracts() -> dict[str, StaticModuleContractBundle]:
    registry: dict[str, StaticModuleContractBundle] = {}
    for module_name in _iter_candidate_module_names():
        for module_id, bundle in _extract_bundles(module_name):
            if module_id in registry:
                raise ValueError(
                    "duplicate framework_module_id in static modules: "
                    f"{module_id} from {bundle.module_type.__module__}"
                )
            registry[module_id] = bundle
    return registry


STATIC_MODULE_CONTRACTS: dict[str, StaticModuleContractBundle] = _build_static_module_contracts()


def reload_static_module_contracts() -> dict[str, StaticModuleContractBundle]:
    for module_name in _iter_candidate_module_names():
        module = importlib.import_module(module_name)
        importlib.reload(module)
    global STATIC_MODULE_CONTRACTS
    STATIC_MODULE_CONTRACTS = _build_static_module_contracts()
    return STATIC_MODULE_CONTRACTS


def get_static_module_contract_bundle(module_id: str) -> StaticModuleContractBundle | None:
    return STATIC_MODULE_CONTRACTS.get(str(module_id))


__all__ = [
    "reload_static_module_contracts",
    "STATIC_MODULE_CONTRACTS",
    "StaticModuleContractBundle",
    "get_static_module_contract_bundle",
]
