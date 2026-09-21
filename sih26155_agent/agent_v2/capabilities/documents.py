"""
Capabilities — Document Generation
GAACA v2.0

generate_markdown: Produces structured markdown reports.
generate_pdf: Placeholder for PDF generation (requires external lib).
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from agent_v2.capabilities.base import (
    ImplementationSpec, CostModel, Observation, ExecContext
)


def _generate_markdown_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Generates a structured markdown report from provided sections."""
    title = params.get("title", "Agent Report")
    sections = params.get("sections", [])
    filename = params.get("filename", "report.md")

    lines = [f"# {title}\n"]
    lines.append(f"*Generated: {datetime.now(timezone.utc).isoformat()}*\n")
    lines.append(f"*Run ID: {ctx.run_id}*\n")
    lines.append("---\n")

    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                heading = section.get("heading", "Section")
                content = section.get("content", "")
                lines.append(f"## {heading}\n")
                lines.append(f"{content}\n")
            elif isinstance(section, str):
                lines.append(f"{section}\n")
    elif isinstance(sections, str):
        lines.append(sections)

    report_text = "\n".join(lines)

    # Write to scratch directory
    output_path = ctx.scratch_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")

    return Observation(
        ok=True,
        output=report_text[:3000],
        metadata={"path": str(output_path), "length": len(report_text)},
    )


def _generate_pdf_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """PDF generation placeholder — falls back to markdown if no PDF library available."""
    # Attempt markdown first, note PDF requirement
    params["filename"] = params.get("filename", "report.md")
    obs = _generate_markdown_handler(params, ctx)

    if obs.ok:
        obs.metadata["note"] = "PDF generation requires external library; markdown produced instead."
    return obs


def register_document_capabilities(registry) -> None:
    """Registers document generation capabilities."""
    registry.register_implementation(ImplementationSpec(
        name="generate_markdown",
        description="Generate structured markdown report from sections",
        input_schema={"title": "str", "sections": "list[dict]", "filename": "str (optional)"},
        output_schema={"report_text": "str", "path": "str"},
        autonomy_action="generate_report",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.5),
        handler=_generate_markdown_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="generate_pdf",
        description="Generate PDF report (falls back to markdown if unavailable)",
        input_schema={"title": "str", "sections": "list[dict]", "filename": "str (optional)"},
        output_schema={"report_text": "str", "path": "str"},
        autonomy_action="generate_report",
        risk="NONE",
        cost=CostModel(estimated_seconds=1.0),
        handler=_generate_pdf_handler,
    ))
