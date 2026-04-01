from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping, cast

from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
    UNSET,
)
from project_runtime.static_modules.common import (
    StaticBaseContract,
    StaticRuleContract,
    _require_boundary_dict,
)

RUNTIME_ENV_L0_M0_MODULE_ID = "runtime_env.L0.M0"
RUNTIME_ENV_L0_M0_MODULE_KEY = "runtime_env__L0__M0"
RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP = {
    "PLATFORM": "platform",
    "CHANNEL": "channel",
    "PERM": "perm",
    "PERF": "perf",
    "NETWORK": "network",
    "POLICY": "policy",
    "FALLBACK": "fallback",
}

@dataclass(frozen=True, slots=True)
class RuntimeEnvL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    platform: object = None
    channel: object = None
    perm: object = None
    perf: object = None
    network: object = None
    policy: object = None
    fallback: object = None

    framework_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    module_key: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class RuntimeEnvL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    platform: object = UNSET
    channel: object = UNSET
    perm: object = UNSET
    perf: object = UNSET
    network: object = UNSET
    policy: object = UNSET
    fallback: object = UNSET

    framework_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    module_key: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP)

class RuntimeEnvL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "runtime_env.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PLATFORM", "CHANNEL", "PERM")

class RuntimeEnvL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "runtime_env.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PERF", "NETWORK", "POLICY")

class RuntimeEnvL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "runtime_env.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FALLBACK", "POLICY", "PERM")

class RuntimeEnvL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("PLATFORM", "CHANNEL", "PERM")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base) -> None:
        self._base_b1 = base_b1

class RuntimeEnvL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1", "runtime_env.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PERF", "NETWORK", "POLICY", "PLATFORM")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base, base_b2: RuntimeEnvL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class RuntimeEnvL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1", "runtime_env.L0.M0.B2", "runtime_env.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FALLBACK", "POLICY", "PERM", "NETWORK")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base, base_b2: RuntimeEnvL0M0B2Base, base_b3: RuntimeEnvL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class RuntimeEnvL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1", "runtime_env.L0.M0.B2", "runtime_env.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PLATFORM", "CHANNEL", "PERM", "PERF", "NETWORK", "POLICY", "FALLBACK")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base, base_b2: RuntimeEnvL0M0B2Base, base_b3: RuntimeEnvL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class RuntimeEnvL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    module_key: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        RuntimeEnvL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        RuntimeEnvL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            RuntimeEnvL0M0B1Base,
            RuntimeEnvL0M0B2Base,
            RuntimeEnvL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            RuntimeEnvL0M0R1Rule,
            RuntimeEnvL0M0R2Rule,
            RuntimeEnvL0M0R3Rule,
            RuntimeEnvL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: RuntimeEnvL0M0StaticBoundaryParams,
        runtime_params: RuntimeEnvL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = RuntimeEnvL0M0B1Base(self)
        self.b2 = RuntimeEnvL0M0B2Base(self)
        self.b3 = RuntimeEnvL0M0B3Base(self)
        self.r1 = RuntimeEnvL0M0R1Rule(self.b1)
        self.r2 = RuntimeEnvL0M0R2Rule(self.b1, self.b2)
        self.r3 = RuntimeEnvL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = RuntimeEnvL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> RuntimeEnvL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, RuntimeEnvL0M0StaticBoundaryParams):
            raise TypeError("RuntimeEnvL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, RuntimeEnvL0M0RuntimeBoundaryParams):
            raise TypeError("RuntimeEnvL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)
