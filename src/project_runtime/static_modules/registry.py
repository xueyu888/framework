from __future__ import annotations

import importlib
import inspect
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
from project_runtime.static_modules import modules as static_module_packages
from project_runtime.static_modules.common import StaticModuleContractBundle

_FRAMEWORK_MODULE_ID_PATTERN = re.compile(r"^[a-z_]+\.[L]\d+\.[M]\d+$")


def _iter_candidate_module_names() -> list[str]:
    prefix = f"{static_module_packages.__name__}."
    names = [
        item.name
        for item in walk_packages(static_module_packages.__path__, prefix=prefix)
        if not item.ispkg
    ]
    names.sort()
    return names


def _own_classes(module: Any) -> list[type[Any]]:
    return [
        item
        for item in vars(module).values()
        if inspect.isclass(item) and item.__module__ == module.__name__
    ]


def _extract_bundle(module_name: str) -> tuple[str, StaticModuleContractBundle] | None:
    module = importlib.import_module(module_name)
    module_types = [
        item
        for item in _own_classes(module)
        if issubclass(item, ModuleContract) and item is not ModuleContract
    ]
    if not module_types:
        return None
    if len(module_types) != 1:
        raise ValueError(
            f"static module file must define exactly one ModuleContract class: "
            f"{module_name} -> {[item.__name__ for item in module_types]}"
        )
    module_type = module_types[0]
    module_id = str(getattr(module_type, "framework_module_id", "")).strip()
    if not _FRAMEWORK_MODULE_ID_PATTERN.match(module_id):
        raise ValueError(f"invalid framework_module_id in {module_name}: {module_id}")

    static_params_type = getattr(module_type, "StaticBoundaryParams", None)
    runtime_params_type = getattr(module_type, "RuntimeBoundaryParams", None)
    base_types = tuple(getattr(module_type, "BaseTypes", tuple()))
    rule_types = tuple(getattr(module_type, "RuleTypes", tuple()))

    if not inspect.isclass(static_params_type) or not issubclass(static_params_type, StaticBoundaryParamsContract):
        raise TypeError(f"invalid StaticBoundaryParams in {module_name}")
    if not inspect.isclass(runtime_params_type) or not issubclass(runtime_params_type, RuntimeBoundaryParamsContract):
        raise TypeError(f"invalid RuntimeBoundaryParams in {module_name}")
    if not all(inspect.isclass(item) and issubclass(item, BaseContract) for item in base_types):
        raise TypeError(f"invalid BaseTypes in {module_name}")
    if not all(inspect.isclass(item) and issubclass(item, RuleContract) for item in rule_types):
        raise TypeError(f"invalid RuleTypes in {module_name}")

    bundle = StaticModuleContractBundle(
        module_type=module_type,
        static_params_type=static_params_type,
        runtime_params_type=runtime_params_type,
        base_types=base_types,
        rule_types=rule_types,
    )
    return module_id, bundle


def _build_static_module_contracts() -> dict[str, StaticModuleContractBundle]:
    registry: dict[str, StaticModuleContractBundle] = {}
    for module_name in _iter_candidate_module_names():
        extracted = _extract_bundle(module_name)
        if extracted is None:
            continue
        module_id, bundle = extracted
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
