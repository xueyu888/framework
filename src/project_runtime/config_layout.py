from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectConfigLayout:
    required_top_level_keys: frozenset[str]
    allowed_top_level_keys: frozenset[str]
    required_nested_tables: dict[str, frozenset[str]]
    allowed_nested_tables: dict[str, frozenset[str]]


def config_layout(
    required_top_level_keys: set[str] | frozenset[str],
    required_nested_tables: dict[str, set[str] | frozenset[str]],
) -> ProjectConfigLayout:
    normalized_required = frozenset(required_top_level_keys)
    normalized_nested = {
        key: frozenset(value)
        for key, value in required_nested_tables.items()
    }
    return ProjectConfigLayout(
        required_top_level_keys=normalized_required,
        allowed_top_level_keys=normalized_required,
        required_nested_tables=normalized_nested,
        allowed_nested_tables=dict(normalized_nested),
    )
