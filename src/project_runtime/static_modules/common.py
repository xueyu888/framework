from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
)


def _require_boundary_dict(payload: dict[str, dict[str, Any]], boundary_id: str) -> dict[str, Any]:
    boundary = payload.get(boundary_id)
    if not isinstance(boundary, dict):
        raise ValueError(f"missing module boundary context: {boundary_id}")
    value = boundary.get("value")
    if not isinstance(value, dict):
        raise ValueError(f"module boundary value must be a dict: {boundary_id}")
    return dict(value)


class StaticBaseContract(BaseContract):
    def __init__(self, module: ModuleContract) -> None:
        self._module = module

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        context = getattr(self._module, "boundary_context", {})
        if not isinstance(context, dict):
            raise ValueError("module boundary context missing")
        return _require_boundary_dict(context, boundary_id)


class StaticRuleContract(RuleContract):
    pass


@dataclass(frozen=True)
class StaticModuleContractBundle:
    module_type: type[ModuleContract]
    static_params_type: type[StaticBoundaryParamsContract]
    runtime_params_type: type[RuntimeBoundaryParamsContract]
    base_types: tuple[type[BaseContract], ...]
    rule_types: tuple[type[RuleContract], ...]


__all__ = [
    "StaticBaseContract",
    "StaticModuleContractBundle",
    "StaticRuleContract",
    "_require_boundary_dict",
]
