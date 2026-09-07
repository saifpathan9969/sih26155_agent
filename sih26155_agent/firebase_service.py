"""
Firebase Firestore Persistence Service for SIH26155 Network Compliance Auditor.

Provides persistent cloud database capabilities for:
- User accounts and roles
- Custom network configurations & audit metadata
- Cryptographic blockchain provenance ledger blocks
- Final compliance audit reports and tamper verification hashes

Graceful Fallback:
If FIREBASE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS is not
provided, the service operates in fallback mode without breaking local or demo workflows.
"""

import os
import json
import base64
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("sih26155.firebase")
logger.setLevel(logging.INFO)

_firebase_app = None
_firestore_db = None
_is_active = False


def init_firebase() -> bool:
    """
    Initialize Firebase Admin SDK using environment variables:
    1. FIREBASE_SERVICE_ACCOUNT_JSON: Inline JSON string, file path, or base64 encoded.
    2. GOOGLE_APPLICATION_CREDENTIALS: Standard file path to service account key.
    """
    global _firebase_app, _firestore_db, _is_active

    if _is_active and _firestore_db is not None:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        logger.warning("[Firebase] firebase-admin package is not installed. Running in local fallback mode.")
        _is_active = False
        return False

    raw_creds = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    g_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

    cred_obj = None

    if raw_creds:
        # Check if it is a file path
        if os.path.isfile(raw_creds):
            try:
                cred_obj = credentials.Certificate(raw_creds)
                logger.info(f"[Firebase] Loaded service account from file path: {raw_creds}")
            except Exception as e:
                logger.error(f"[Firebase] Failed to load credentials from file path: {e}")
        else:
            # Check if it is base64 encoded
            parsed_json = None
            try:
                decoded = base64.b64decode(raw_creds).decode("utf-8")
                parsed_json = json.loads(decoded)
                logger.info("[Firebase] Successfully decoded base64 service account JSON.")
            except Exception:
                # Raw JSON string
                try:
                    parsed_json = json.loads(raw_creds)
                    logger.info("[Firebase] Successfully parsed inline service account JSON.")
                except Exception as e:
                    logger.error(f"[Firebase] Could not parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

            if parsed_json:
                try:
                    cred_obj = credentials.Certificate(parsed_json)
                except Exception as e:
                    logger.error(f"[Firebase] Error creating certificate from parsed JSON: {e}")

    elif g_creds_path and os.path.isfile(g_creds_path):
        try:
            cred_obj = credentials.Certificate(g_creds_path)
            logger.info(f"[Firebase] Loaded service account from GOOGLE_APPLICATION_CREDENTIALS: {g_creds_path}")
        except Exception as e:
            logger.error(f"[Firebase] Error loading GOOGLE_APPLICATION_CREDENTIALS: {e}")

    if cred_obj:
        try:
            if not firebase_admin._apps:
                _firebase_app = firebase_admin.initialize_app(cred_obj)
            else:
                _firebase_app = firebase_admin.get_app()
            _firestore_db = firestore.client()
            _is_active = True
            logger.info("[Firebase] Firestore database connected successfully!")
            return True
        except Exception as e:
            logger.error(f"[Firebase] Failed to initialize Firebase App: {e}")
            _is_active = False
            return False

    logger.info("[Firebase] No cloud credentials detected. Running in-memory / local fallback mode.")
    _is_active = False
    return False


def is_active() -> bool:
    """Check if Firebase Firestore is active and ready."""
    return _is_active and _firestore_db is not None


# ---------------------------------------------------------------------------
# User Accounts Persistence
# ---------------------------------------------------------------------------

def save_user(user_data: dict) -> bool:
    """Save or update user document in 'users' collection."""
    if not is_active():
        return False
    try:
        username = (user_data.get("username") or user_data.get("email") or "").strip().lower()
        if not username:
            return False
        _firestore_db.collection("users").document(username).set(user_data, merge=True)
        return True
    except Exception as e:
        logger.error(f"[Firebase] Error saving user {user_data.get('username')}: {e}")
        return False


def get_user(username_or_email: str) -> Optional[dict]:
    """Retrieve user document from 'users' collection."""
    if not is_active():
        return None
    try:
        key = username_or_email.strip().lower()
        doc = _firestore_db.collection("users").document(key).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"[Firebase] Error fetching user {username_or_email}: {e}")
        return None


def get_all_users() -> List[dict]:
    """Retrieve all users stored in Firestore."""
    if not is_active():
        return []
    try:
        docs = _firestore_db.collection("users").stream()
        return [d.to_dict() for d in docs]
    except Exception as e:
        logger.error(f"[Firebase] Error fetching all users: {e}")
        return []


# ---------------------------------------------------------------------------
# Configurations Persistence
# ---------------------------------------------------------------------------

def save_config(username: str, filename: str, content: str, metadata: dict) -> bool:
    """Save user configuration and its parsed metadata."""
    if not is_active():
        return False
    try:
        uname = username.strip().lower()
        doc_id = f"{uname}__{filename}"
        payload = {
            "username": uname,
            "filename": filename,
            "content": content,
            "metadata": metadata,
            "updated_at": firestore.SERVER_TIMESTAMP if _firestore_db else None,
        }
        _firestore_db.collection("configurations").document(doc_id).set(payload, merge=True)
        return True
    except Exception as e:
        logger.error(f"[Firebase] Error saving configuration {filename}: {e}")
        return False


def get_user_configs(username: str) -> Dict[str, dict]:
    """Retrieve all configurations uploaded by a user."""
    if not is_active():
        return {}
    try:
        uname = username.strip().lower()
        docs = _firestore_db.collection("configurations").where("username", "==", uname).stream()
        results = {}
        for d in docs:
            data = d.to_dict()
            fname = data.get("filename")
            if fname:
                results[fname] = {
                    "content": data.get("content", ""),
                    "metadata": data.get("metadata", {}),
                }
        return results
    except Exception as e:
        logger.error(f"[Firebase] Error fetching user configs for {username}: {e}")
        return {}


def delete_config(username: str, filename: str) -> bool:
    """Delete configuration document."""
    if not is_active():
        return False
    try:
        uname = username.strip().lower()
        doc_id = f"{uname}__{filename}"
        _firestore_db.collection("configurations").document(doc_id).delete()
        return True
    except Exception as e:
        logger.error(f"[Firebase] Error deleting config {filename}: {e}")
        return False


# ---------------------------------------------------------------------------
# Blockchain Ledger Persistence
# ---------------------------------------------------------------------------

def save_blockchain_block(block_dict: dict) -> bool:
    """Record an immutable block in the Firestore 'blockchain_ledger' collection."""
    if not is_active():
        return False
    try:
        idx = block_dict.get("index", 0)
        doc_id = f"block_{idx:06d}"
        _firestore_db.collection("blockchain_ledger").document(doc_id).set(block_dict)
        return True
    except Exception as e:
        logger.error(f"[Firebase] Error saving blockchain block #{block_dict.get('index')}: {e}")
        return False


def get_all_blockchain_blocks() -> List[dict]:
    """Load all saved blockchain blocks ordered by index."""
    if not is_active():
        return []
    try:
        docs = _firestore_db.collection("blockchain_ledger").order_by("index").stream()
        return [d.to_dict() for d in docs]
    except Exception as e:
        logger.error(f"[Firebase] Error fetching blockchain ledger: {e}")
        return []


# ---------------------------------------------------------------------------
# Audit Reports Persistence
# ---------------------------------------------------------------------------

def save_audit_report(report_id: str, report_data: dict) -> bool:
    """Store audit mission report and tamper-evident SHA-256 hash."""
    if not is_active():
        return False
    try:
        _firestore_db.collection("audit_reports").document(report_id).set(report_data)
        # Also mark as latest
        _firestore_db.collection("audit_reports").document("latest").set(report_data)
        return True
    except Exception as e:
        logger.error(f"[Firebase] Error saving audit report {report_id}: {e}")
        return False


def get_latest_audit_report() -> Optional[dict]:
    """Retrieve the latest audit report."""
    if not is_active():
        return None
    try:
        doc = _firestore_db.collection("audit_reports").document("latest").get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"[Firebase] Error fetching latest report: {e}")
        return None
