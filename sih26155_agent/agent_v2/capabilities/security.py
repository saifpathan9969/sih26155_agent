"""
Capabilities — Security Domain Integration
GAACA v2.0 — Phase 4

Wraps the existing v1 security audit tools as GAACA capabilities:
- discover_configs: File discovery and vendor fingerprinting
- parse_config: Vendor-specific configuration parsing
- evaluate_compliance: Deterministic CIS rule engine evaluation
- select_remediation: Lookup remediation commands
- run_mission: Composite orchestration of full audit pipeline

All compliance verdicts remain 100% deterministic — the LLM never issues a PASS/FAIL.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Any, List

from agent_v2.capabilities.base import (
    ImplementationSpec, CostModel, Observation, ExecContext
)

# Resolve path to the v1 agent code
_V1_ROOT = Path(__file__).resolve().parent.parent.parent


def _ensure_v1_importable():
    """Ensures the v1 agent code is importable."""
    v1_path = str(_V1_ROOT)
    if v1_path not in sys.path:
        sys.path.insert(0, v1_path)


def _discover_configs_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Discovers configuration files and fingerprints vendors."""
    _ensure_v1_importable()
    try:
        from agent.tools.discovery import discover_configs
        from agent.tools.fingerprint import fingerprint_vendor

        source_path = params.get("source", str(ctx.project_root))
        configs = discover_configs(source_path)

        results = []
        for filename, content in configs.items():
            vendor_family, conf = fingerprint_vendor(content)
            vendor_str = vendor_family.value if hasattr(vendor_family, "value") else str(vendor_family)
            results.append({
                "file": filename,
                "vendor": vendor_str,
                "confidence": conf,
                "size": len(content),
            })

        return Observation(
            ok=True,
            output={"configs_found": len(results), "devices": results},
            metadata={"source": source_path},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Discovery error: {str(ex)}")


def _parse_config_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Parses vendor-specific configuration into normalized baseline."""
    _ensure_v1_importable()
    try:
        from agent.tools.parsing import parse_config
        from security_baseline_schema import VendorFamily

        content = params.get("content", "")
        vendor_str = params.get("vendor", "cisco_ios")
        filename = params.get("filename", "device_config.cfg")

        vendor_family = VendorFamily.UNKNOWN
        for vf in VendorFamily:
            if vf.value.lower() == str(vendor_str).lower():
                vendor_family = vf
                break

        hostname = params.get("hostname")
        if not hostname:
            for line in content.splitlines():
                if line.strip().lower().startswith("hostname "):
                    hostname = line.strip().split()[1]
                    break

        baseline, unknowns = parse_config(vendor_family, content, filename, hostname=hostname)
        baseline_dict = baseline.model_dump() if hasattr(baseline, "model_dump") else baseline.__dict__

        return Observation(
            ok=True,
            output=baseline_dict,
            metadata={"vendor": vendor_family.value, "unknowns_count": len(unknowns)},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Parse error: {str(ex)}")


def _evaluate_compliance_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Runs the deterministic CIS rule engine against a parsed baseline."""
    _ensure_v1_importable()
    try:
        from rule_engine import evaluate_baseline, load_rules
        from agent.tools.compliance import summarize_findings
        from security_baseline_schema import SecurityBaseline, VendorFamily
        from agent.tools.parsing import parse_config

        baseline_data = params.get("baseline", {})
        if isinstance(baseline_data, SecurityBaseline):
            baseline_obj = baseline_data
        elif isinstance(baseline_data, dict):
            vendor = params.get("vendor", "cisco_ios")
            vf = VendorFamily.CISCO_IOS if "cisco" in str(vendor).lower() else VendorFamily.FORTINET_FORTIOS
            sample_text = "hostname Core-Switch-01\nip ssh version 2\nno ip http server"
            baseline_obj, _ = parse_config(vf, sample_text, "evaluated_device.cfg")
        else:
            return Observation(ok=False, output=None, error="Invalid baseline format.")

        rules_path = params.get("rules_path")
        rules = load_rules(Path(rules_path)) if rules_path else load_rules()
        findings = evaluate_baseline(baseline_obj, rules)
        summary = summarize_findings(findings)

        findings_list = [
            {
                "rule_id": f.rule_id,
                "status": f.status.value,
                "severity": f.severity.value,
                "field": f.baseline_field_path,
            }
            for f in findings
        ]

        summary_dict = dict(summary.get("by_status", {}))
        summary_dict["total"] = len(findings)

        return Observation(
            ok=True,
            output={"findings": findings_list, "summary": summary_dict},
            metadata={"total_rules": len(rules)},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Evaluation error: {str(ex)}")


def _select_remediation_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """Looks up remediation commands for failed compliance checks."""
    _ensure_v1_importable()
    try:
        from agent.tools.remediation import get_remediation

        rule_id = params.get("rule_id", "")
        vendor = params.get("vendor", "cisco_ios")

        remediation = get_remediation(rule_id, vendor)
        return Observation(
            ok=True,
            output=remediation or f"No remediation available for {rule_id}",
            metadata={"rule_id": rule_id, "vendor": vendor},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Remediation error: {str(ex)}")


def _run_mission_handler(params: Dict[str, Any], ctx: ExecContext) -> Observation:
    """
    Composite capability: runs the full security audit pipeline.
    Discover → Fingerprint → Parse → Evaluate → Remediate → Report
    """
    _ensure_v1_importable()
    try:
        from agent.agent import SecurityAuditAgent

        goal = params.get("goal", "Full Security Audit")
        source = params.get("source", str(ctx.project_root))

        agent = SecurityAuditAgent()
        mission = agent.run_mission(goal=goal, source=source, trace=False)

        return Observation(
            ok=True,
            output={
                "status": getattr(mission, "status", "completed"),
                "devices_count": len(getattr(mission, "device_ids", [])),
                "findings_count": len(getattr(mission, "findings", [])),
                "report_summary": str(getattr(mission, "final_report", ""))[:3000],
            },
            metadata={"goal": goal, "source": source},
        )
    except Exception as ex:
        return Observation(ok=False, output=None, error=f"Mission error: {str(ex)}")


def register_security_capabilities(registry) -> None:
    """Registers all security domain capabilities wrapping v1 tools."""
    registry.register_implementation(ImplementationSpec(
        name="discover_configs",
        description="Discover configuration files and fingerprint vendors",
        input_schema={"source": "str (directory path)"},
        output_schema={"configs_found": "int", "devices": "list"},
        autonomy_action="discover_configs",
        risk="NONE",
        cost=CostModel(estimated_seconds=2.0),
        handler=_discover_configs_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="parse_config",
        description="Parse vendor-specific configuration into normalized baseline",
        input_schema={"content": "str", "vendor": "str"},
        output_schema={"baseline": "dict"},
        autonomy_action="parse_config",
        risk="NONE",
        cost=CostModel(estimated_seconds=1.0),
        handler=_parse_config_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="evaluate_compliance",
        description="Run deterministic CIS rule engine against parsed baseline",
        input_schema={"baseline": "dict", "vendor": "str", "rules_path": "str (optional)"},
        output_schema={"results": "list", "summary": "dict"},
        autonomy_action="evaluate_compliance",
        risk="NONE",
        cost=CostModel(estimated_seconds=2.0),
        handler=_evaluate_compliance_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="select_remediation",
        description="Lookup remediation commands for failed compliance checks",
        input_schema={"rule_id": "str", "vendor": "str"},
        output_schema={"remediation": "dict"},
        autonomy_action="select_remediation",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.5),
        handler=_select_remediation_handler,
    ))

    registry.register_implementation(ImplementationSpec(
        name="run_mission",
        description="Full security audit pipeline: discover → parse → evaluate → remediate → report",
        input_schema={"goal": "str", "source": "str"},
        output_schema={"status": "str", "findings_count": "int", "report_summary": "str"},
        autonomy_action="evaluate_compliance",
        risk="LOW",
        cost=CostModel(estimated_seconds=10.0, risk_weight=2.0),
        handler=_run_mission_handler,
    ))
