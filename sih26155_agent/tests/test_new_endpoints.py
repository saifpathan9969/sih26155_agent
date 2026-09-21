import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "agent"))
sys.path.insert(1, str(_ROOT))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_auth_endpoints():
    # Test pre-seeded login
    res = client.post("/api/auth/login", json={"username": "admin", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["user"]["role"] == "Lead Security Auditor"

    # Test invalid login
    res_bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert res_bad.status_code == 401

    # Test new registration
    res_reg = client.post("/api/auth/register", json={
        "username": "new_auditor",
        "password": "securepassword",
        "role": "Compliance Auditor",
        "organization": "NTRO Cyber Command",
        "full_name": "Major V. Singh"
    })
    assert res_reg.status_code == 200
    assert res_reg.json()["user"]["username"] == "new_auditor"


def test_configuration_upload_and_management():
    # Ingest new custom configuration
    cisco_snippet = """
    hostname edge-router-99
    service password-encryption
    security passwords min-length 14
    ip ssh version 2
    """
    upload_res = client.post("/api/configurations/upload", json={
        "filename": "edge_router_99.conf",
        "content": cisco_snippet,
        "vendor": "cisco_ios"
    })
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["success"] is True
    assert data["filename"] == "edge_router_99.conf"
    assert data["vendor"] == "cisco_ios"

    # Verify present in get_configurations
    list_res = client.get("/api/configurations")
    assert list_res.status_code == 200
    configs = list_res.json()["configurations"]
    fnames = [c["filename"] for c in configs]
    assert "edge_router_99.conf" in fnames

    # Delete custom configuration
    del_res = client.delete("/api/configurations/edge_router_99.conf")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_mission_with_device_selection():
    # Run audit targeting specifically dev01 and dev02
    res = client.post("/api/mission/run", json={
        "goal": "Audit Cisco devices only",
        "selected_devices": ["dev01_cisco.conf", "dev02_cisco.conf"]
    })
    assert res.status_code == 200
    data = res.json()
    assert "audited_devices" in data
    assert set(data["audited_devices"]) == {"dev01_cisco.conf", "dev02_cisco.conf"}
    assert "dev01_cisco.conf" in data["findings_by_device"]
    assert "dev02_cisco.conf" in data["findings_by_device"]
    assert "dev03_juniper.conf" not in data["findings_by_device"]


def test_human_review_resolution_and_blockchain_sealing():
    # Submit a human review resolution
    res = client.post("/api/human-review/resolve", json={
        "device_id": "dev03_juniper.conf",
        "rule_id": "CIS-AUTH-03",
        "command_raw": "set system login retry-options tries-before-disconnect 5",
        "decision": "PASS",
        "notes": "Verified against Junos 21.4 security hardening documentation.",
        "uploaded_info": "Parameter enforces lockout after 5 consecutive failures.",
        "reviewer": "Commander A. Sharma"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["decision"] == "PASS"
    assert data["after_status"] == "pass"
    assert "blockchain_block_index" in data
    assert data["blockchain_block_index"] > 0


def test_guide_assistant_chatbot():
    # Ask about blockchain hashes
    res = client.post("/api/guide/chat", json={
        "message": "Why are hashes on the blockchain page and what is their use?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "SHA-256" in data["reply"]
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0
