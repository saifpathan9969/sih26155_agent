"""
Blockchain Cryptographic Integrity Ledger — SIH26155
=====================================================
Theme: Blockchain & Cybersecurity (NTRO)

CRITICAL ARCHITECTURAL BOUNDARY:
- Blockchain is an immutable provenance and tamper-detection layer ONLY.
- It records cryptographic hashes of approved rules, two-person approvals,
  and final audit reports.
- It NEVER evaluates compliance, NEVER replaces the deterministic rule engine,
  and NEVER decides security verdicts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BlockchainBlock:
    index: int
    timestamp: str
    previous_hash: str
    event_type: str  # "GENESIS" | "RULE_APPROVAL" | "REPORT_INTEGRITY" | "KNOWLEDGE_CONFIRMATION"
    payload: Dict[str, Any]
    block_hash: str
    nonce: int = 0

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "event_type": self.event_type,
            "payload": self.payload,
            "block_hash": self.block_hash,
            "nonce": self.nonce,
        }


def compute_block_hash(
    index: int,
    timestamp: str,
    previous_hash: str,
    event_type: str,
    payload: Dict[str, Any],
    nonce: int = 0,
) -> str:
    canonical = {
        "index": index,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
        "event_type": event_type,
        "payload": payload,
        "nonce": nonce,
    }
    serialized = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_data_hash(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class BlockchainLedger:
    def __init__(self) -> None:
        self.chain: List[BlockchainBlock] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        ts = "2026-09-01T00:00:00.000000Z"
        prev = "0" * 64
        payload = {
            "system": "SIH26155 Multi-Vendor Network Compliance Auditor",
            "organization": "NTRO",
            "genesis_notice": "Cryptographic Trust Anchor & Provenance Ledger",
        }
        bhash = compute_block_hash(0, ts, prev, "GENESIS", payload, nonce=0)
        genesis = BlockchainBlock(
            index=0,
            timestamp=ts,
            previous_hash=prev,
            event_type="GENESIS",
            payload=payload,
            block_hash=bhash,
            nonce=0,
        )
        self.chain.append(genesis)

    def record_rule_approval(
        self,
        rule_id: str,
        version: int,
        rule_hash: str,
        approvers: List[Dict[str, str]],
        rationale: str,
    ) -> BlockchainBlock:
        payload = {
            "rule_id": rule_id,
            "version": version,
            "rule_sha256": rule_hash,
            "approvers": approvers,
            "rationale": rationale,
            "approval_count": len(approvers),
            "status": "APPROVED_AND_ACTIVATED",
        }
        return self._add_block("RULE_APPROVAL", payload)

    def record_report_integrity(
        self,
        report_id: str,
        report_text: str,
        goal: str,
        summary: dict,
    ) -> Tuple[BlockchainBlock, str]:
        report_hash = compute_data_hash(report_text)
        payload = {
            "report_id": report_id,
            "report_sha256": report_hash,
            "goal": goal,
            "summary": summary,
            "report_length_bytes": len(report_text.encode("utf-8")),
        }
        block = self._add_block("REPORT_INTEGRITY", payload)
        return block, report_hash

    def record_knowledge_confirmation(
        self,
        vendor: str,
        raw_pattern: str,
        baseline_field_path: str,
        confirmed_by: str,
    ) -> BlockchainBlock:
        payload = {
            "vendor": vendor,
            "raw_pattern": raw_pattern,
            "baseline_field_path": baseline_field_path,
            "confirmed_by": confirmed_by,
            "pattern_sha256": compute_data_hash(raw_pattern),
        }
        return self._add_block("KNOWLEDGE_CONFIRMATION", payload)

    def record_human_decision(
        self,
        device_id: str,
        rule_id: str,
        command_raw: str,
        decision: str,
        reviewer: str,
        notes: Optional[str] = None,
        uploaded_info: Optional[str] = None,
    ) -> BlockchainBlock:
        payload = {
            "device_id": device_id,
            "rule_id": rule_id,
            "command_raw": command_raw,
            "command_hash": compute_data_hash(command_raw),
            "decision": decision,
            "reviewer": reviewer,
            "notes": notes or "",
            "has_uploaded_info": bool(uploaded_info),
            "uploaded_info_hash": compute_data_hash(uploaded_info) if uploaded_info else "",
        }
        return self._add_block("HUMAN_DECISION", payload)


    def _add_block(self, event_type: str, payload: Dict[str, Any]) -> BlockchainBlock:
        prev_block = self.chain[-1]
        index = len(self.chain)
        timestamp = datetime.now(timezone.utc).isoformat()
        previous_hash = prev_block.block_hash
        block_hash = compute_block_hash(index, timestamp, previous_hash, event_type, payload, nonce=0)

        block = BlockchainBlock(
            index=index,
            timestamp=timestamp,
            previous_hash=previous_hash,
            event_type=event_type,
            payload=payload,
            block_hash=block_hash,
            nonce=0,
        )
        self.chain.append(block)
        try:
            import firebase_service
            if firebase_service.is_active():
                firebase_service.save_blockchain_block(block.to_dict())
        except Exception:
            pass
        return block

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Cryptographically verifies the entire ledger from genesis to head:
        1. Checks previous_hash chaining.
        2. Recalculates block_hash for every block and verifies equality.
        """
        for i in range(len(self.chain)):
            block = self.chain[i]
            # Verify hash recalculation
            expected_hash = compute_block_hash(
                block.index,
                block.timestamp,
                block.previous_hash,
                block.event_type,
                block.payload,
                block.nonce,
            )
            if block.block_hash != expected_hash:
                return False, f"Block {i} hash mismatch: recorded={block.block_hash}, calculated={expected_hash}"

            # Verify chain linkage
            if i > 0:
                prev_block = self.chain[i - 1]
                if block.previous_hash != prev_block.block_hash:
                    return False, f"Block {i} broken link: prev_hash={block.previous_hash} != {prev_block.block_hash}"

        return True, None

    def verify_report(self, report_text: str, expected_hash: str) -> bool:
        current_hash = compute_data_hash(report_text)
        return current_hash == expected_hash

    def simulate_tamper(
        self,
        original_report: str,
        target_rule: str = "CIS-MGMT-01",
        fake_status: str = "PASS",
    ) -> Dict[str, Any]:
        """
        Hero moment simulation:
        Alters a reported finding (e.g. FAIL -> PASS) in the report content,
        recalculates the SHA-256 hash, and compares against the immutable on-chain record.
        """
        stored_block = next(
            (b for b in reversed(self.chain) if b.event_type == "REPORT_INTEGRITY"),
            None,
        )
        stored_hash = stored_block.payload["report_sha256"] if stored_block else compute_data_hash(original_report)

        # Deliberately modify finding text
        tampered_report = original_report.replace(
            f"`{target_rule}` (critical) —",
            f"`{target_rule}` [TAMPERED TO {fake_status}] —",
        )
        if tampered_report == original_report:
            # Fallback modification
            tampered_report = original_report + f"\n\n<!-- TAMPERED: {target_rule} marked as {fake_status} -->\n"

        tampered_hash = compute_data_hash(tampered_report)
        is_valid = (tampered_hash == stored_hash)

        return {
            "stored_hash": stored_hash,
            "current_hash": tampered_hash,
            "tamper_detected": not is_valid,
            "status": "TAMPER DETECTED" if not is_valid else "VERIFIED",
            "explanation": (
                "The current report hash does not match the immutable hash committed "
                "to the blockchain ledger. Content has been modified after audit finalization."
                if not is_valid else "Report matches on-chain commitment."
            ),
            "original_report": original_report,
            "tampered_report": tampered_report,
        }

    def get_ledger(self) -> List[dict]:
        return [b.to_dict() for b in self.chain]
