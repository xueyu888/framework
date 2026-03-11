from __future__ import annotations

from framework_core import (
    Base,
    BoundaryDefinition,
    BoundaryItem,
    Capability,
    VerificationInput,
    VerificationResult,
    verify,
)


DOCUMENT_CHUNKING_TEMPLATE_CAPABILITIES = (
    Capability("C1", "稳定声明段落分界模板、信号集合与模板版本。"),
    Capability("C2", "稳定执行分界命中并产出可排序命中结果。"),
    Capability("C3", "稳定输出统一的命中结果与失败原因结构。"),
)

DOCUMENT_CHUNKING_TEMPLATE_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("TEMPLATE", "模板名称、版本与启停状态必须稳定。"),
        BoundaryItem("SIGNAL", "分界信号、命中条件与优先级必须明确。"),
        BoundaryItem("WINDOW", "命中窗口、偏移校验与冲突裁决范围必须明确。"),
        BoundaryItem("RESULT", "命中结果、失败原因与命中偏移结构必须统一。"),
    )
)

DOCUMENT_CHUNKING_TEMPLATE_BASES = (
    Base("B1", "模板定义结构基", "template metadata + signal catalog"),
    Base("B2", "命中判定结构基", "signal evaluation + window validation"),
    Base("B3", "命中结果结构基", "hit offset + window range + result status"),
)


def compose_boundary_template(template_id: str = "default") -> dict[str, object]:
    return {
        "template_id": template_id,
        "signals": ["heading_prefix", "blank_line_gap"],
        "window_policy": "single_document_window",
        "result_schema": ["hit_offset", "window_range", "result_status"],
    }


def verify_boundary_template(template_id: str = "default") -> VerificationResult:
    payload = VerificationInput(
        subject=f"boundary-template:{template_id}",
        pass_criteria=[
            "template metadata is present",
            "signals are non-empty",
            "result schema is stable",
        ],
        evidence=compose_boundary_template(template_id),
    )
    return verify(payload)


PARAGRAPH_BLOCK_CAPABILITIES = (
    Capability("C1", "稳定承载段落块文本、顺序与原文定位。"),
    Capability("C2", "稳定承载段落块角色状态与角色解释。"),
    Capability("C3", "稳定登记段落块归属关系与回溯信息。"),
)

PARAGRAPH_BLOCK_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("BLOCK", "段落文本、块标识与定位信息必须完整。"),
        BoundaryItem("ORDER", "段落块顺序必须稳定且不可跳序。"),
        BoundaryItem("ROLE", "角色值、判型状态与角色解释必须稳定。"),
        BoundaryItem("OWNERSHIP", "归属关系必须唯一且可回放。"),
        BoundaryItem("TRACE", "来源、角色变化与归属变化必须可追踪。"),
    )
)

PARAGRAPH_BLOCK_BASES = (
    Base("B1", "段落块承载基", "block payload + order index"),
    Base("B2", "角色标注结构基", "role state + role explanation"),
    Base("B3", "归属登记结构基", "owner chunk id + position + trace token"),
)


def compose_paragraph_block_flow(block_count: int = 1) -> dict[str, object]:
    normalized_count = max(block_count, 1)
    return {
        "block_count": normalized_count,
        "labeled_block_fields": ["block_id", "order_index", "block_role"],
        "ownership_fields": ["block_id", "owner_chunk_id", "position_in_chunk"],
        "trace_enabled": True,
    }


def verify_paragraph_block_flow(block_count: int = 1) -> VerificationResult:
    payload = VerificationInput(
        subject=f"paragraph-block-flow:{max(block_count, 1)}",
        pass_criteria=[
            "paragraph blocks are ordered",
            "roles are explicit",
            "ownership is unique",
        ],
        evidence=compose_paragraph_block_flow(block_count),
    )
    return verify(payload)
