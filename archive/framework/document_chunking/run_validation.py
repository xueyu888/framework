from __future__ import annotations

from pathlib import Path
import json

from document_chunking_generated import dump_json, process_document


REPO_ROOT = Path(__file__).resolve().parents[2]
RES_DIR = Path(__file__).resolve().parent / "res"

INPUTS = {
    "framework_design_core_standard": REPO_ROOT / "specs/框架设计核心标准.md",
    "framework_doc_lint_standard": REPO_ROOT / "specs/框架文档Lint标准.md",
}


def render_chunk_markdown(alias: str, source_path: Path, output) -> str:
    lines = [
        f"# {alias} Chunk View",
        "",
        f"- source: `{source_path.as_posix()}`",
        f"- paragraph blocks: `{len(output.paragraph_block_set)}`",
        f"- text chunks: `{len(output.text_chunk_set)}`",
        "",
    ]

    for index, chunk in enumerate(output.text_chunk_set, start=1):
        if index > 1:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )
        lines.extend(
            [
                f"<!-- chunk:{chunk.text_chunk_id} start -->",
                f"## {chunk.text_chunk_id}",
                "",
                f"- title_block_id: `{chunk.title_block_id}`",
                f"- body_block_count: `{len(chunk.body_block_id_set)}`",
                f"- order_range: `{chunk.start_order}..{chunk.end_order}`",
                "",
                chunk.text,
                f"<!-- chunk:{chunk.text_chunk_id} end -->",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    RES_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {"documents": {}, "all_passed": True}
    report_lines = ["# Document Chunking Validation", ""]

    for alias, source_path in INPUTS.items():
        output, report = process_document(source_path)

        output_path = RES_DIR / f"{alias}.chunks.json"
        report_path = RES_DIR / f"{alias}.validation.json"
        markdown_path = RES_DIR / f"{alias}.chunks.md"
        dump_json(output_path, output.to_dict())
        dump_json(report_path, report.to_dict())
        markdown_path.write_text(render_chunk_markdown(alias, source_path, output), encoding="utf-8")

        summary["documents"][alias] = {
            "source_path": source_path.as_posix(),
            "chunks_path": output_path.as_posix(),
            "validation_path": report_path.as_posix(),
            "markdown_path": markdown_path.as_posix(),
            "passed": report.passed,
            "chunk_count": len(output.text_chunk_set),
            "paragraph_block_count": len(output.paragraph_block_set),
            "invalid_record_count": len(output.invalid_set),
        }
        summary["all_passed"] = bool(summary["all_passed"]) and report.passed

        report_lines.append(f"## {alias}")
        report_lines.append("")
        report_lines.append(f"- source: `{source_path.as_posix()}`")
        report_lines.append(f"- passed: `{report.passed}`")
        report_lines.append(f"- paragraph blocks: `{len(output.paragraph_block_set)}`")
        report_lines.append(f"- text chunks: `{len(output.text_chunk_set)}`")
        report_lines.append(f"- invalid records: `{len(output.invalid_set)}`")
        report_lines.append("")
        report_lines.append("### Validation Items")
        report_lines.append("")
        for item in report.items:
            reasons = "; ".join(item.reasons) if item.reasons else "none"
            report_lines.append(f"- `{item.validation_id}`: `{item.passed}`; reasons: `{reasons}`")
        report_lines.append("")

    summary_path = RES_DIR / "validation_summary.json"
    summary_report_path = RES_DIR / "validation_report.md"
    dump_json(summary_path, summary)
    summary_report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
