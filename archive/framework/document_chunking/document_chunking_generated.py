from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any


class BlockRole(str, Enum):
    TITLE = "title"
    BODY = "body"


@dataclass(frozen=True)
class ParagraphBlock:
    block_id: str
    order_index: int
    text: str
    start_offset: int
    end_offset: int
    block_role: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChunkMatch:
    text_chunk_id: str
    title_block_id: str
    body_block_id_set: tuple[str, ...]
    start_order: int
    end_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OwnershipRecord:
    block_id: str
    text_chunk_id: str
    block_role: str
    position_in_chunk: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TextChunk:
    text_chunk_id: str
    title_block_id: str
    body_block_id_set: tuple[str, ...]
    start_order: int
    end_order: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentChunkingOutput:
    text_chunk_set: tuple[TextChunk, ...]
    ownership_record_set: tuple[OwnershipRecord, ...]
    paragraph_block_set: tuple[ParagraphBlock, ...]
    trace_meta: dict[str, Any]
    invalid_set: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_chunk_set": [item.to_dict() for item in self.text_chunk_set],
            "ownership_record_set": [item.to_dict() for item in self.ownership_record_set],
            "paragraph_block_set": [item.to_dict() for item in self.paragraph_block_set],
            "trace_meta": self.trace_meta,
            "invalid_set": list(self.invalid_set),
        }


@dataclass(frozen=True)
class ValidationItem:
    validation_id: str
    passed: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "passed": self.passed,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class ValidationReport:
    document_name: str
    source_path: str
    passed: bool
    items: tuple[ValidationItem, ...]
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_name": self.document_name,
            "source_path": self.source_path,
            "passed": self.passed,
            "items": [item.to_dict() for item in self.items],
            "evidence": self.evidence,
        }


class TemporaryBoundaryTemplate:
    """Temporary substitute for B1 when L3 only states the need for explicit segmentation."""

    template_id = "TEMP-B1-blank-line-splitter"
    description = "Split normalized markdown text on blank-line paragraph boundaries."

    def split(self, text: str) -> tuple[ParagraphBlock, ...]:
        blocks: list[ParagraphBlock] = []
        lines = text.splitlines(keepends=True)
        current_lines: list[str] = []
        current_start: int | None = None
        offset = 0

        for line in lines:
            is_blank = line.strip() == ""
            if not is_blank:
                if current_start is None:
                    current_start = offset
                current_lines.append(line)
            elif current_lines:
                blocks.append(self._build_block(current_lines, current_start, len(blocks) + 1))
                current_lines = []
                current_start = None
            offset += len(line)

        if current_lines:
            blocks.append(self._build_block(current_lines, current_start, len(blocks) + 1))

        return tuple(blocks)

    def _build_block(
        self,
        lines: list[str],
        start_offset: int | None,
        order_index: int,
    ) -> ParagraphBlock:
        joined = "".join(lines)
        text = joined.strip()
        actual_start = 0 if start_offset is None else start_offset
        end_offset = actual_start + len(joined)
        return ParagraphBlock(
            block_id=f"pb-{order_index:04d}",
            order_index=order_index,
            text=text,
            start_offset=actual_start,
            end_offset=end_offset,
        )


class TemporaryRoleJudgeModule:
    """Temporary substitute for B3 when L3 does not specify the concrete role judge."""

    classifier_id = "TEMP-B3-markdown-role-judge"
    HEADING_PATTERN = re.compile(
        r"^(#{1,6}\s+.+|[0-9]+(\.[0-9]+)*[.)]?\s+.+|第[一二三四五六七八九十百千0-9]+[章节部分篇].+)$"
    )

    def label(self, blocks: tuple[ParagraphBlock, ...]) -> tuple[ParagraphBlock, ...]:
        labeled: list[ParagraphBlock] = []
        for block in blocks:
            role = self._classify(block.text)
            labeled.append(
                ParagraphBlock(
                    block_id=block.block_id,
                    order_index=block.order_index,
                    text=block.text,
                    start_offset=block.start_offset,
                    end_offset=block.end_offset,
                    block_role=role.value,
                )
            )
        return tuple(labeled)

    def _classify(self, text: str) -> BlockRole:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return BlockRole.BODY

        first_line = lines[0]
        single_line = len(lines) == 1
        if self.HEADING_PATTERN.match(first_line):
            return BlockRole.TITLE
        if single_line and not first_line.startswith(("-", "*", "+", ">")):
            if len(first_line) <= 48 and not re.search(r"[。！？；：:,.;!?]$", first_line):
                return BlockRole.TITLE
        return BlockRole.BODY


class TemporaryChunkMatcher:
    """Temporary substitute for B4 when L3 only constrains title+following-body grouping."""

    matcher_id = "TEMP-B4-title-body-matcher"

    def match(
        self,
        blocks: tuple[ParagraphBlock, ...],
    ) -> tuple[tuple[ChunkMatch, ...], tuple[dict[str, Any], ...]]:
        matches: list[ChunkMatch] = []
        invalids: list[dict[str, Any]] = []
        current_title: ParagraphBlock | None = None
        current_bodies: list[ParagraphBlock] = []

        for block in blocks:
            if block.block_role == BlockRole.TITLE.value:
                if current_title is not None:
                    matches.append(self._build_chunk_match(current_title, current_bodies, len(matches) + 1))
                current_title = block
                current_bodies = []
                continue

            if current_title is None:
                invalids.append(
                    {
                        "invalid_id": f"ir-{len(invalids) + 1:04d}",
                        "rule": "R6",
                        "block_id": block.block_id,
                        "reason": "body_block_without_title_anchor",
                    }
                )
                continue

            current_bodies.append(block)

        if current_title is not None:
            matches.append(self._build_chunk_match(current_title, current_bodies, len(matches) + 1))

        return tuple(matches), tuple(invalids)

    def _build_chunk_match(
        self,
        title_block: ParagraphBlock,
        body_blocks: list[ParagraphBlock],
        order_index: int,
    ) -> ChunkMatch:
        body_ids = tuple(block.block_id for block in body_blocks)
        end_order = body_blocks[-1].order_index if body_blocks else title_block.order_index
        return ChunkMatch(
            text_chunk_id=f"tc-{order_index:04d}",
            title_block_id=title_block.block_id,
            body_block_id_set=body_ids,
            start_order=title_block.order_index,
            end_order=end_order,
        )


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip()


def build_output(
    source_path: Path,
    paragraph_blocks: tuple[ParagraphBlock, ...],
    chunk_matches: tuple[ChunkMatch, ...],
    invalids: tuple[dict[str, Any], ...],
) -> DocumentChunkingOutput:
    block_by_id = {block.block_id: block for block in paragraph_blocks}
    text_chunks: list[TextChunk] = []
    ownership_records: list[OwnershipRecord] = []

    for match in chunk_matches:
        title_block = block_by_id[match.title_block_id]
        ordered_blocks = [title_block, *[block_by_id[block_id] for block_id in match.body_block_id_set]]
        text_chunks.append(
            TextChunk(
                text_chunk_id=match.text_chunk_id,
                title_block_id=match.title_block_id,
                body_block_id_set=match.body_block_id_set,
                start_order=match.start_order,
                end_order=match.end_order,
                text="\n\n".join(block.text for block in ordered_blocks),
            )
        )

        for position, block in enumerate(ordered_blocks, start=1):
            ownership_records.append(
                OwnershipRecord(
                    block_id=block.block_id,
                    text_chunk_id=match.text_chunk_id,
                    block_role=block.block_role or BlockRole.BODY.value,
                    position_in_chunk=position,
                )
            )

    trace_meta = {
        "source_path": source_path.as_posix(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "temporary_modules": {
            "B1": TemporaryBoundaryTemplate.template_id,
            "B3": TemporaryRoleJudgeModule.classifier_id,
            "B4": TemporaryChunkMatcher.matcher_id,
        },
    }
    return DocumentChunkingOutput(
        text_chunk_set=tuple(text_chunks),
        ownership_record_set=tuple(ownership_records),
        paragraph_block_set=paragraph_blocks,
        trace_meta=trace_meta,
        invalid_set=invalids,
    )


def validate_output(output: DocumentChunkingOutput) -> ValidationReport:
    paragraph_blocks = output.paragraph_block_set
    chunk_matches = output.trace_meta.get("chunk_match_set", [])
    ownership_records = output.ownership_record_set
    invalids = output.invalid_set

    items: list[ValidationItem] = []

    v1_reasons: list[str] = []
    if not output.trace_meta.get("source_path"):
        v1_reasons.append("missing_source_path")
    if not paragraph_blocks:
        v1_reasons.append("no_paragraph_blocks")
    items.append(ValidationItem("V1", not v1_reasons, tuple(v1_reasons)))

    v2_reasons: list[str] = []
    seen_orders: set[int] = set()
    seen_ranges: list[tuple[int, int, str]] = []
    for block in paragraph_blocks:
        if not block.text.strip():
            v2_reasons.append(f"empty_text:{block.block_id}")
        if block.order_index in seen_orders:
            v2_reasons.append(f"duplicate_order:{block.block_id}")
        seen_orders.add(block.order_index)
        if block.start_offset >= block.end_offset:
            v2_reasons.append(f"invalid_range:{block.block_id}")
        for start, end, other_id in seen_ranges:
            if not (block.end_offset <= start or block.start_offset >= end):
                v2_reasons.append(f"overlap:{block.block_id}:{other_id}")
        seen_ranges.append((block.start_offset, block.end_offset, block.block_id))
    items.append(ValidationItem("V2", not v2_reasons, tuple(v2_reasons)))

    v3_reasons: list[str] = []
    for block in paragraph_blocks:
        if block.block_role not in {BlockRole.TITLE.value, BlockRole.BODY.value}:
            v3_reasons.append(f"invalid_role:{block.block_id}")
    items.append(ValidationItem("V3", not v3_reasons, tuple(v3_reasons)))

    v4_reasons: list[str] = []
    consumed: set[str] = set()
    for match in chunk_matches:
        all_ids = [match["title_block_id"], *match["body_block_id_set"]]
        if match["start_order"] > match["end_order"]:
            v4_reasons.append(f"invalid_order_window:{match['text_chunk_id']}")
        for block_id in all_ids:
            if block_id in consumed:
                v4_reasons.append(f"reused_block:{block_id}")
            consumed.add(block_id)
    items.append(ValidationItem("V4", not v4_reasons and not invalids, tuple(v4_reasons)))

    v5_reasons: list[str] = []
    ownership_by_block: dict[str, str] = {}
    for record in ownership_records:
        existing = ownership_by_block.get(record.block_id)
        if existing and existing != record.text_chunk_id:
            v5_reasons.append(f"multi_chunk_ownership:{record.block_id}")
        ownership_by_block[record.block_id] = record.text_chunk_id
    for chunk in output.text_chunk_set:
        expected_ids = {chunk.title_block_id, *chunk.body_block_id_set}
        actual_ids = {record.block_id for record in ownership_records if record.text_chunk_id == chunk.text_chunk_id}
        if expected_ids != actual_ids:
            v5_reasons.append(f"ownership_mismatch:{chunk.text_chunk_id}")
    items.append(ValidationItem("V5", not v5_reasons, tuple(v5_reasons)))

    v6_reasons: list[str] = []
    if not output.text_chunk_set:
        v6_reasons.append("empty_text_chunk_set")
    if not output.ownership_record_set:
        v6_reasons.append("empty_ownership_record_set")
    if not output.trace_meta.get("chunk_match_set"):
        v6_reasons.append("missing_chunk_match_trace")
    items.append(ValidationItem("V6", not v6_reasons, tuple(v6_reasons)))

    v7_reasons: list[str] = []
    for invalid in invalids:
        if not invalid.get("invalid_id") or not invalid.get("reason"):
            v7_reasons.append("invalid_record_missing_fields")
    items.append(ValidationItem("V7", not v7_reasons, tuple(v7_reasons)))

    v8_reasons: list[str] = []
    minimality_matrix = {
        "B1": ("V2",),
        "B2": ("V2", "V6"),
        "B3": ("V3", "V4"),
        "B4": ("V4", "V5", "V6"),
        "B5": ("V5", "V6"),
        "B6": ("V6",),
    }
    if set(minimality_matrix) != {"B1", "B2", "B3", "B4", "B5", "B6"}:
        v8_reasons.append("incomplete_minimality_matrix")
    items.append(ValidationItem("V8", not v8_reasons, tuple(v8_reasons)))

    v9_reasons: list[str] = []
    if len(items) != 8:
        v9_reasons.append("missing_intermediate_validations")
    items.append(ValidationItem("V9", not v9_reasons, tuple(v9_reasons)))

    passed = all(item.passed for item in items)
    return ValidationReport(
        document_name=Path(output.trace_meta["source_path"]).stem,
        source_path=output.trace_meta["source_path"],
        passed=passed,
        items=tuple(items),
        evidence={
            "paragraph_block_count": len(paragraph_blocks),
            "text_chunk_count": len(output.text_chunk_set),
            "ownership_record_count": len(ownership_records),
            "invalid_record_count": len(invalids),
            "chunk_match_count": len(chunk_matches),
            "minimality_matrix": minimality_matrix,
        },
    )


def process_document(source_path: Path) -> tuple[DocumentChunkingOutput, ValidationReport]:
    normalized = normalize_text(source_path.read_text(encoding="utf-8"))

    boundary_template = TemporaryBoundaryTemplate()
    role_judge = TemporaryRoleJudgeModule()
    matcher = TemporaryChunkMatcher()

    paragraph_blocks = boundary_template.split(normalized)
    labeled_blocks = role_judge.label(paragraph_blocks)
    chunk_matches, invalids = matcher.match(labeled_blocks)

    output = build_output(source_path, labeled_blocks, chunk_matches, invalids)
    output.trace_meta["chunk_match_set"] = [item.to_dict() for item in chunk_matches]
    report = validate_output(output)
    return output, report


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
