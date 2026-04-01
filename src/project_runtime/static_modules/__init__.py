"""Static per-module implementations used by the runtime compiler."""

from project_runtime.static_modules.registry import (
    STATIC_MODULE_CONTRACTS,
    StaticModuleContractBundle,
    get_static_module_contract_bundle,
)

__all__ = [
    "STATIC_MODULE_CONTRACTS",
    "StaticModuleContractBundle",
    "get_static_module_contract_bundle",
]
