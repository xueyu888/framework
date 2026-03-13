from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from typing import Any


TITLE_ROLE = "title"
BODY_ROLE = "body"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _default_text_id(document_name: str, text: str) -> str:
    stem = Path(document_name).stem.strip()
    return stem or f"doc-{_sha256_text(text)[:12]}"


def _markdown_fence(text: str) -> str:
    max_backticks = 3
    for match in re.finditer(r"`+", text):
        max_backticks = max(max_backticks, len(match.group(0)) + 1)
    return "`" * max_backticks


def normalize_document_text(text: str) -> str:
    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    normalized_lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(normalized_lines).strip()


@dataclass(frozen=True)
class ParagraphBlock:
    block_id: str
    order_index: int
    text: str
    start_offset: int
    end_offset: int
    document_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LabeledParagraphBlock:
    block_id: str
    order_index: int
    text: str
    start_offset: int
    end_offset: int
    document_id: str
    block_role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChunkMatch:
    text_chunk_id: str
    chunk_id: int
    title_block_id: str
    body_block_id_set: tuple[str, ...]
    ordered_block_id_set: tuple[str, ...]
    start_order: int
    end_order: int
    closure_reason: str
    chunk_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_chunk_id": self.text_chunk_id,
            "chunk_id": self.chunk_id,
            "title_block_id": self.title_block_id,
            "body_block_id_set": list(self.body_block_id_set),
            "ordered_block_id_set": list(self.ordered_block_id_set),
            "start_order": self.start_order,
            "end_order": self.end_order,
            "closure_reason": self.closure_reason,
            "chunk_text": self.chunk_text,
        }


@dataclass(frozen=True)
class OwnershipRecord:
    block_id: str
    text_chunk_id: str
    block_role: str
    position_in_chunk: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChunkItem:
    chunk_id: int
    chunk_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InvalidCombination:
    invalid_reason: str
    offending_object_id_set: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "invalid_reason": self.invalid_reason,
            "offending_object_id_set": list(self.offending_object_id_set),
        }


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    checks: tuple[ValidationCheck, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [item.to_dict() for item in self.checks],
        }


@dataclass(frozen=True)
class DocumentChunkingOutput:
    text_id: str
    ordered_chunk_item_set: tuple[ChunkItem, ...]
    ownership_record_set: tuple[OwnershipRecord, ...]
    paragraph_block_set: tuple[ParagraphBlock, ...]
    trace_meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_id": self.text_id,
            "ordered_chunk_item_set": [item.to_dict() for item in self.ordered_chunk_item_set],
            "ownership_record_set": [item.to_dict() for item in self.ownership_record_set],
            "paragraph_block_set": [item.to_dict() for item in self.paragraph_block_set],
            "trace_meta": self.trace_meta,
        }


@dataclass(frozen=True)
class DocumentChunkingRunResult:
    document_name: str
    text_id: str
    normalized_text_sha256: str
    paragraph_block_set: tuple[ParagraphBlock, ...]
    labeled_paragraph_block_set: tuple[LabeledParagraphBlock, ...]
    chunk_match_set: tuple[ChunkMatch, ...]
    ownership_record_set: tuple[OwnershipRecord, ...]
    invalid_combination_set: tuple[InvalidCombination, ...]
    output: DocumentChunkingOutput
    validation: ValidationReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_name": self.document_name,
            "text_id": self.text_id,
            "normalized_text_sha256": self.normalized_text_sha256,
            "paragraph_block_set": [item.to_dict() for item in self.paragraph_block_set],
            "labeled_paragraph_block_set": [item.to_dict() for item in self.labeled_paragraph_block_set],
            "chunk_match_set": [item.to_dict() for item in self.chunk_match_set],
            "ownership_record_set": [item.to_dict() for item in self.ownership_record_set],
            "invalid_combination_set": [item.to_dict() for item in self.invalid_combination_set],
            "output": self.output.to_dict(),
            "validation": self.validation.to_dict(),
        }


def render_document_chunking_output_markdown(
    result: DocumentChunkingRunResult,
    *,
    text_id_field: str = "text_id",
    chunk_id_field: str = "chunk_id",
    chunk_text_field: str = "chunk_text",
) -> str:
    lines = [f"{text_id_field}: {result.output.text_id}", ""]
    for chunk_item in result.output.ordered_chunk_item_set:
        fence = _markdown_fence(chunk_item.chunk_text)
        lines.append(f"{chunk_id_field}: {chunk_item.chunk_id}")
        lines.append(f"{chunk_text_field}:")
        lines.append(f"{fence}markdown")
        lines.extend(chunk_item.chunk_text.splitlines())
        lines.append(fence)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_paragraph_blocks(
    text: str,
    *,
    document_id: str,
    max_block_chars: int,
) -> tuple[ParagraphBlock, ...]:
    blocks: list[ParagraphBlock] = []
    position = 0
    block_start: int | None = None
    last_content_end: int | None = None
    order_index = 1

    for raw_line in text.splitlines(keepends=True):
        line_start = position
        position += len(raw_line)
        if raw_line.strip():
            if block_start is None:
                block_start = line_start
            last_content_end = position
            continue

        if block_start is None or last_content_end is None:
            continue

        end_offset = last_content_end
        while end_offset > block_start and text[end_offset - 1] == "\n":
            end_offset -= 1
        block_text = text[block_start:end_offset]
        if not block_text:
            block_start = None
            last_content_end = None
            continue
        if len(block_text) > max_block_chars:
            raise ValueError(
                f"paragraph block length exceeds max_block_chars={max_block_chars}: {len(block_text)}"
            )
        blocks.append(
            ParagraphBlock(
                block_id=f"{document_id}-pb-{order_index:04d}",
                order_index=order_index,
                text=block_text,
                start_offset=block_start,
                end_offset=end_offset,
                document_id=document_id,
            )
        )
        order_index += 1
        block_start = None
        last_content_end = None

    if block_start is not None and last_content_end is not None:
        end_offset = last_content_end
        while end_offset > block_start and text[end_offset - 1] == "\n":
            end_offset -= 1
        block_text = text[block_start:end_offset]
        if block_text:
            if len(block_text) > max_block_chars:
                raise ValueError(
                    f"paragraph block length exceeds max_block_chars={max_block_chars}: {len(block_text)}"
                )
            blocks.append(
                ParagraphBlock(
                    block_id=f"{document_id}-pb-{order_index:04d}",
                    order_index=order_index,
                    text=block_text,
                    start_offset=block_start,
                    end_offset=end_offset,
                    document_id=document_id,
                )
            )

    return tuple(blocks)


def label_paragraph_blocks(
    blocks: tuple[ParagraphBlock, ...],
    *,
    heading_pattern: str,
) -> tuple[LabeledParagraphBlock, ...]:
    compiled_heading_pattern = re.compile(heading_pattern)
    labeled_blocks: list[LabeledParagraphBlock] = []
    for block in blocks:
        first_line = block.text.splitlines()[0].strip() if block.text else ""
        block_role = TITLE_ROLE if compiled_heading_pattern.match(first_line) else BODY_ROLE
        labeled_blocks.append(
            LabeledParagraphBlock(
                block_id=block.block_id,
                order_index=block.order_index,
                text=block.text,
                start_offset=block.start_offset,
                end_offset=block.end_offset,
                document_id=block.document_id,
                block_role=block_role,
            )
        )
    return tuple(labeled_blocks)


def compose_text_chunks(
    labeled_blocks: tuple[LabeledParagraphBlock, ...],
    *,
    text_id: str,
) -> tuple[tuple[ChunkMatch, ...], tuple[InvalidCombination, ...]]:
    chunk_matches: list[ChunkMatch] = []
    invalids: list[InvalidCombination] = []
    current_title: LabeledParagraphBlock | None = None
    current_bodies: list[LabeledParagraphBlock] = []
    chunk_id = 1

    def close_current_chunk(closure_reason: str) -> None:
        nonlocal chunk_id, current_title, current_bodies
        if current_title is None:
            return
        ordered_blocks = [current_title, *current_bodies]
        chunk_matches.append(
            ChunkMatch(
                text_chunk_id=f"{text_id}-chunk-{chunk_id:04d}",
                chunk_id=chunk_id,
                title_block_id=current_title.block_id,
                body_block_id_set=tuple(item.block_id for item in current_bodies),
                ordered_block_id_set=tuple(item.block_id for item in ordered_blocks),
                start_order=current_title.order_index,
                end_order=ordered_blocks[-1].order_index,
                closure_reason=closure_reason,
                chunk_text="\n\n".join(item.text for item in ordered_blocks),
            )
        )
        chunk_id += 1
        current_title = None
        current_bodies = []

    for block in labeled_blocks:
        if block.block_role == TITLE_ROLE:
            if current_title is not None:
                close_current_chunk("next_title")
            current_title = block
            current_bodies = []
            continue

        if current_title is None:
            invalids.append(
                InvalidCombination(
                    invalid_reason="body block cannot form a chunk before the first title block",
                    offending_object_id_set=(block.block_id,),
                )
            )
            continue

        current_bodies.append(block)

    if current_title is not None:
        close_current_chunk("document_end")

    return tuple(chunk_matches), tuple(invalids)


def build_ownership_records(
    labeled_blocks: tuple[LabeledParagraphBlock, ...],
    chunk_matches: tuple[ChunkMatch, ...],
) -> tuple[OwnershipRecord, ...]:
    labeled_by_id = {item.block_id: item for item in labeled_blocks}
    ownership_records: list[OwnershipRecord] = []
    for chunk_match in chunk_matches:
        for position_in_chunk, block_id in enumerate(chunk_match.ordered_block_id_set, start=1):
            labeled_block = labeled_by_id[block_id]
            ownership_records.append(
                OwnershipRecord(
                    block_id=block_id,
                    text_chunk_id=chunk_match.text_chunk_id,
                    block_role=labeled_block.block_role,
                    position_in_chunk=position_in_chunk,
                )
            )
    return tuple(ownership_records)


def build_output(
    *,
    document_name: str,
    text_id: str,
    paragraph_blocks: tuple[ParagraphBlock, ...],
    labeled_blocks: tuple[LabeledParagraphBlock, ...],
    chunk_matches: tuple[ChunkMatch, ...],
    ownership_records: tuple[OwnershipRecord, ...],
    invalids: tuple[InvalidCombination, ...],
) -> DocumentChunkingOutput:
    trace_meta = {
        "document_name": document_name,
        "labeled_paragraph_block_set": [item.to_dict() for item in labeled_blocks],
        "chunk_match_set": [item.to_dict() for item in chunk_matches],
        "invalid_combination_set": [item.to_dict() for item in invalids],
    }
    return DocumentChunkingOutput(
        text_id=text_id,
        ordered_chunk_item_set=tuple(
            ChunkItem(chunk_id=item.chunk_id, chunk_text=item.chunk_text)
            for item in chunk_matches
        ),
        ownership_record_set=ownership_records,
        paragraph_block_set=paragraph_blocks,
        trace_meta=trace_meta,
    )


def validate_document_chunking_result(
    result: DocumentChunkingRunResult,
    *,
    max_chunk_items: int,
) -> ValidationReport:
    paragraph_blocks = result.paragraph_block_set
    labeled_blocks = result.labeled_paragraph_block_set
    chunk_matches = result.chunk_match_set
    ownership_records = result.ownership_record_set
    ordered_chunk_items = result.output.ordered_chunk_item_set

    checks: list[ValidationCheck] = []

    unique_order_indexes = {item.order_index for item in paragraph_blocks}
    paragraph_blocks_are_valid = (
        bool(paragraph_blocks)
        and len(unique_order_indexes) == len(paragraph_blocks)
        and all(item.start_offset >= 0 and item.end_offset > item.start_offset for item in paragraph_blocks)
        and all(bool(item.text.strip()) for item in paragraph_blocks)
    )
    checks.append(
        ValidationCheck(
            check_id="V1",
            passed=paragraph_blocks_are_valid,
            detail="paragraph blocks keep unique order indexes, valid offsets, and non-empty text",
        )
    )

    roles_are_valid = all(item.block_role in {TITLE_ROLE, BODY_ROLE} for item in labeled_blocks)
    checks.append(
        ValidationCheck(
            check_id="V2",
            passed=roles_are_valid,
            detail="labeled paragraph blocks only use title/body role values",
        )
    )

    chunk_matches_are_valid = bool(chunk_matches) and not result.invalid_combination_set and all(
        match.ordered_block_id_set
        and match.title_block_id == match.ordered_block_id_set[0]
        and match.start_order <= match.end_order
        and list(match.ordered_block_id_set) == [match.title_block_id, *match.body_block_id_set]
        for match in chunk_matches
    )
    checks.append(
        ValidationCheck(
            check_id="V3",
            passed=chunk_matches_are_valid,
            detail="each chunk match starts with one title block and then zero or more ordered body blocks",
        )
    )

    ownership_by_block = {item.block_id: item.text_chunk_id for item in ownership_records}
    grouped_block_ids = {
        block_id
        for match in chunk_matches
        for block_id in match.ordered_block_id_set
    }
    ownership_is_consistent = (
        len(ownership_by_block) == len(ownership_records)
        and grouped_block_ids == set(ownership_by_block)
        and all(item.position_in_chunk >= 1 for item in ownership_records)
    )
    checks.append(
        ValidationCheck(
            check_id="V4",
            passed=ownership_is_consistent,
            detail="ownership table covers every grouped paragraph block exactly once",
        )
    )

    output_is_valid = (
        bool(result.output.text_id)
        and len(ordered_chunk_items) <= max_chunk_items
        and all(item.chunk_id >= 1 and bool(item.chunk_text.strip()) for item in ordered_chunk_items)
        and [item.chunk_id for item in ordered_chunk_items] == list(range(1, len(ordered_chunk_items) + 1))
    )
    checks.append(
        ValidationCheck(
            check_id="V5",
            passed=output_is_valid,
            detail="output keeps text_id and ordered (chunk_id, chunk_text) pairs within count limits",
        )
    )

    trace_is_valid = (
        result.output.trace_meta.get("document_name") == result.document_name
        and len(result.output.paragraph_block_set) == len(paragraph_blocks)
        and len(result.output.ownership_record_set) == len(ownership_records)
    )
    checks.append(
        ValidationCheck(
            check_id="V6",
            passed=trace_is_valid,
            detail="output remains traceable back to paragraph blocks and ownership records",
        )
    )

    passed = all(item.passed for item in checks)
    return ValidationReport(passed=passed, checks=tuple(checks))


def run_document_chunking_pipeline(
    *,
    document_name: str,
    text: str,
    text_id: str | None = None,
    heading_pattern: str = r"^(#{1,6})\s+.+$",
    max_block_chars: int = 8000,
    max_chunk_items: int = 2000,
) -> DocumentChunkingRunResult:
    normalized_text = normalize_document_text(text)
    resolved_text_id = text_id or _default_text_id(document_name, normalized_text)
    paragraph_blocks = build_paragraph_blocks(
        normalized_text,
        document_id=resolved_text_id,
        max_block_chars=max_block_chars,
    )
    labeled_blocks = label_paragraph_blocks(
        paragraph_blocks,
        heading_pattern=heading_pattern,
    )
    chunk_matches, invalids = compose_text_chunks(
        labeled_blocks,
        text_id=resolved_text_id,
    )
    ownership_records = build_ownership_records(labeled_blocks, chunk_matches)
    output = build_output(
        document_name=document_name,
        text_id=resolved_text_id,
        paragraph_blocks=paragraph_blocks,
        labeled_blocks=labeled_blocks,
        chunk_matches=chunk_matches,
        ownership_records=ownership_records,
        invalids=invalids,
    )
    provisional_result = DocumentChunkingRunResult(
        document_name=document_name,
        text_id=resolved_text_id,
        normalized_text_sha256=_sha256_text(normalized_text),
        paragraph_block_set=paragraph_blocks,
        labeled_paragraph_block_set=labeled_blocks,
        chunk_match_set=chunk_matches,
        ownership_record_set=ownership_records,
        invalid_combination_set=invalids,
        output=output,
        validation=ValidationReport(passed=False, checks=()),
    )
    validation = validate_document_chunking_result(
        provisional_result,
        max_chunk_items=max_chunk_items,
    )
    return DocumentChunkingRunResult(
        document_name=document_name,
        text_id=resolved_text_id,
        normalized_text_sha256=_sha256_text(normalized_text),
        paragraph_block_set=paragraph_blocks,
        labeled_paragraph_block_set=labeled_blocks,
        chunk_match_set=chunk_matches,
        ownership_record_set=ownership_records,
        invalid_combination_set=invalids,
        output=output,
        validation=validation,
    )


def run_document_chunking_pipeline_on_file(
    input_file: str | Path,
    *,
    text_id: str | None = None,
    heading_pattern: str = r"^(#{1,6})\s+.+$",
    max_block_chars: int = 8000,
    max_chunk_items: int = 2000,
) -> DocumentChunkingRunResult:
    resolved_file = Path(input_file).resolve()
    text = resolved_file.read_text(encoding="utf-8")
    return run_document_chunking_pipeline(
        document_name=resolved_file.name,
        text=text,
        text_id=text_id or resolved_file.stem,
        heading_pattern=heading_pattern,
        max_block_chars=max_block_chars,
        max_chunk_items=max_chunk_items,
    )
