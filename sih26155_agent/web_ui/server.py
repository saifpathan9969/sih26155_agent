"""
VigilNet v2.0 — Web UI Server
Flask backend that wraps the autonomous cognitive agent
and exposes REST API endpoints for the 3D web interface.
"""

import sys
import os
import json
import uuid
import threading
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

# Ensure agent_v2 is importable
_INNER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_INNER_ROOT))

from agent_v2.core.agent import AutonomousAgent
from agent_v2.core.task_registry import GLOBAL_TASK_REGISTRY

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Agent singleton ──────────────────────────────────────────────────
_agent = None
_agent_lock = threading.Lock()


def _get_agent() -> AutonomousAgent:
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                _agent = AutonomousAgent(
                    project_root=_INNER_ROOT,
                    scratch_dir=_INNER_ROOT / "scratch",
                    approval_callback=None,
                    trace_to_console=False,
                    enable_security=True,
                )
                _agent.register_all_capabilities()
    return _agent


# ── Pages ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/report/download")
@app.route("/api/report/pdf")
def download_pdf():
    pdf_path = _INNER_ROOT / "compliance_audit_report_2026-09-19.pdf"
    if not pdf_path.exists():
        from report_to_pdf import build_pdf, parse_report
        data = parse_report("")
        build_pdf(data, str(pdf_path))
    return send_file(
        str(pdf_path),
        as_attachment=True,
        download_name="compliance_audit_report_2026-09-19.pdf",
        mimetype="application/pdf",
    )


# ── Chat API ─────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    agent = _get_agent()
    try:
        with _agent_lock:
            state = agent.run(message, max_cycles=10)

        # Collect cycle trace
        cycles = []
        for rec in state.trace:
            cycles.append({
                "cycle": rec.cycle_index,
                "subgoal": rec.what_i_need,
                "action": rec.action_decided,
                "observation": str(rec.observation_summary)[:300] if rec.observation_summary else "",
                "beliefs": rec.epistemic_delta,
            })

        # Collect conversational reply if any
        reply = None
        for act in state.completed_actions:
            if act.implementation == "converse":
                reply = act.observation
                break

        return jsonify({
            "ok": True,
            "reply": reply,
            "terminal_state": state.terminal_state.value,
            "justification": state.terminal_justification,
            "completed_actions": len(state.completed_actions),
            "failed_actions": len(state.failed_actions),
            "cycles": cycles,
            "actions": [
                {
                    "cycle": a.cycle,
                    "capability": a.capability,
                    "implementation": a.implementation,
                    "observation": str(a.observation)[:500] if a.observation else "",
                    "ok": a.ok,
                }
                for a in state.completed_actions
            ],
            "failures": [
                {
                    "cycle": f.cycle,
                    "action": f.action,
                    "error": f.error,
                    "failure_class": f.failure_class,
                    "diagnosis": f.diagnosis,
                }
                for f in state.failed_actions
            ],
        })
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 500


# ── File Upload API ──────────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No file selected"}), 400

    safe_name = f"{uuid.uuid4().hex[:8]}_{f.filename}"
    save_path = UPLOAD_DIR / safe_name
    f.save(str(save_path))

    return jsonify({
        "ok": True,
        "filename": f.filename,
        "saved_as": safe_name,
        "path": str(save_path),
        "size_bytes": save_path.stat().st_size,
    })


# ── File List API ────────────────────────────────────────────────────
@app.route("/api/uploads", methods=["GET"])
def list_uploads():
    """Return all uploaded files so the sidebar survives page refreshes."""
    files = []
    for p in sorted(UPLOAD_DIR.iterdir()):
        if p.is_file():
            # Recover original filename (strip the 8-char hex prefix + underscore)
            name = p.name
            original = name[9:] if len(name) > 9 and name[8] == "_" else name
            files.append({
                "ok": True,
                "filename": original,
                "saved_as": name,
                "path": str(p),
                "size_bytes": p.stat().st_size,
            })
    return jsonify(files)


# ── File Delete API ──────────────────────────────────────────────────
@app.route("/api/upload/<path:saved_name>", methods=["DELETE"])
def delete_upload(saved_name):
    """Delete an uploaded file by its saved_as name."""
    target = UPLOAD_DIR / saved_name

    # Prevent path traversal
    try:
        target = target.resolve()
        if not str(target).startswith(str(UPLOAD_DIR.resolve())):
            return jsonify({"ok": False, "error": "Invalid path"}), 400
    except Exception:
        return jsonify({"ok": False, "error": "Invalid path"}), 400

    if not target.exists():
        return jsonify({"ok": False, "error": "File not found"}), 404

    try:
        target.unlink()
        return jsonify({"ok": True, "deleted": saved_name})
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 500


# ── Status / Introspection APIs ─────────────────────────────────────
@app.route("/api/status")
def status():
    agent = _get_agent()
    info = agent.inspect()
    return jsonify({
        "status": agent.status(),
        "capabilities": info["registry"]["capabilities"],
        "implementations": info["registry"]["implementations"],
        "episodic_episodes": info["memory"]["episodic_episodes"],
        "semantic_concepts": info["memory"]["semantic_concepts"],
        "procedural_patterns": info["memory"]["procedural_patterns"],
        "tasks": info.get("tasks", {}),
    })


@app.route("/api/capabilities")
def capabilities():
    agent = _get_agent()
    caps = agent.registry.all_capabilities()
    return jsonify([
        {
            "name": c.name,
            "description": c.description,
            "implementations": c.implementations,
        }
        for c in caps
    ])


@app.route("/api/memory")
def memory():
    agent = _get_agent()
    wm = agent.working_memory.summary()
    eps = agent.episodic_memory.last_n(10)
    return jsonify({
        "working": wm,
        "recent_episodes": [
            {
                "run_id": e.run_id,
                "cycle": e.cycle_index,
                "action": e.action_taken,
                "success": e.success,
                "surprise": e.surprise_score,
            }
            for e in eps
        ],
        "total_episodes": agent.episodic_memory.total_episodes(),
    })


@app.route("/api/beliefs")
def beliefs():
    agent = _get_agent()
    facts = agent.semantic_memory.all_facts()
    return jsonify([
        {
            "subject": f.subject,
            "value": str(f.value)[:200],
            "source": f.source,
            "confidence": f.confidence,
        }
        for f in facts[:30]
    ])


@app.route("/api/hypotheses")
def hypotheses():
    agent = _get_agent()
    engine = agent.executive.hypothesis_engine
    all_h = list(engine.hypotheses.values())
    return jsonify([
        {
            "id": h.id,
            "statement": h.statement,
            "status": h.status,
            "prior": h.prior,
            "posterior": h.posterior,
            "supporting": len(h.supporting),
            "refuting": len(h.refuting),
        }
        for h in all_h
    ])


@app.route("/api/patterns")
def patterns():
    agent = _get_agent()
    pats = agent.learning_engine.all_patterns()
    return jsonify([
        {
            "description": p.description,
            "type": p.pattern_type,
            "validation": p.validation_method.value,
            "citable": p.is_citable,
            "retired": p.retired,
            "contradictions": p.contradiction_count,
        }
        for p in pats
    ])


@app.route("/api/tasks")
def tasks():
    all_tasks = GLOBAL_TASK_REGISTRY.list_tasks()
    return jsonify({
        "summary": GLOBAL_TASK_REGISTRY.summary(),
        "tasks": [t.to_dict() for t in all_tasks],
    })


# ── Run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  VigilNet v2.0 — 3D Web Interface")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
