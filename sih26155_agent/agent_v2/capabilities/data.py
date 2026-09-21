"""
Capabilities — Data Analysis
GAACA v2.0

load_dataset: Load structured data from CSV/JSON/YAML files.
analyze: Basic statistical analysis on loaded data.
summarize_stats: Produce summary statistics.
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Dict, Any, List

from agent_v2.capabilities.base import (
    ImplementationSpec, CostModel, Observation, ExecContext
)


def _load_dataset_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Loads structured data from a file within the project."""
    path_str = params.get("path", "")
    target = (ctx.project_root / path_str).resolve()

    if not target.is_relative_to(ctx.project_root):
        return Observation(ok=False, output=None, error="Path escapes project boundary.")
    if not target.exists():
        return Observation(ok=False, output=None, error=f"File not found: {path_str}")

    suffix = target.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(target.read_text(encoding="utf-8"))
        elif suffix in (".yaml", ".yml"):
            import yaml
            data = yaml.safe_load(target.read_text(encoding="utf-8"))
        elif suffix == ".csv":
            with open(target, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            content = target.read_text(encoding="utf-8", errors="replace")
            data = {"raw_text": content[:5000], "lines": content.count("\n") + 1}

        record_count = len(data) if isinstance(data, list) else 1

        return Observation(
            ok=True,
            output=data if record_count <= 100 else data[:100],
            metadata={"format": suffix, "records": record_count, "path": str(target)},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Load error: {str(ex)}")


def _analyze_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Basic analysis on structured data passed as input."""
    data = params.get("data", [])
    field_name = params.get("field", None)

    if not isinstance(data, list) or len(data) == 0:
        return Observation(ok=False, output=None, error="No list data provided for analysis.")

    result: Dict[str, Any] = {"total_records": len(data)}

    if isinstance(data[0], dict):
        result["fields"] = list(data[0].keys())

        if field_name and field_name in data[0]:
            values = [row.get(field_name) for row in data if row.get(field_name) is not None]
            numeric = []
            for v in values:
                try:
                    numeric.append(float(v))
                except (ValueError, TypeError):
                    pass

            if numeric:
                result[f"{field_name}_stats"] = {
                    "count": len(numeric),
                    "min": min(numeric),
                    "max": max(numeric),
                    "mean": round(sum(numeric) / len(numeric), 4),
                    "sum": round(sum(numeric), 4),
                }
            else:
                unique = set(str(v) for v in values)
                result[f"{field_name}_unique_values"] = len(unique)
                result[f"{field_name}_sample"] = list(unique)[:10]

    return Observation(ok=True, output=result)


def _summarize_stats_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Produces a text summary of data statistics."""
    data = params.get("data", {})
    title = params.get("title", "Data Summary")

    lines = [f"### {title}"]
    if isinstance(data, dict):
        for key, value in data.items():
            lines.append(f"- **{key}**: {value}")
    elif isinstance(data, list):
        lines.append(f"- Records: {len(data)}")
        if data and isinstance(data[0], dict):
            lines.append(f"- Fields: {', '.join(data[0].keys())}")

    summary = "\n".join(lines)
    return Observation(ok=True, output=summary)


def register_data_capabilities(registry) -> None:
    """Registers data loading and analysis capabilities."""
    registry.register_implementation(ImplementationSpec(
        name="load_dataset",
        description="Load structured data from CSV/JSON/YAML within project",
        input_schema={"path": "str"},
        output_schema={"data": "list|dict", "records": "int"},
        autonomy_action="read_file",
        risk="NONE",
        cost=CostModel(estimated_seconds=1.0),
        handler=_load_dataset_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="analyze_data",
        description="Basic statistical analysis on structured data",
        input_schema={"data": "list", "field": "str (optional)"},
        output_schema={"stats": "dict"},
        autonomy_action="inspect_project",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.5),
        handler=_analyze_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="summarize_stats",
        description="Produce text summary of data statistics",
        input_schema={"data": "dict|list", "title": "str (optional)"},
        output_schema={"summary": "str"},
        autonomy_action="generate_report",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.3),
        handler=_summarize_stats_handler,
    ))
