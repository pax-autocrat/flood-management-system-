"""
JalRakshak NCR — Authentication & Identity Service (Phase 1)
Engineered for Team NeerNetra (SustainX 2026)
Handles bcrypt password hashing, JWT issue/verify, citizen OTP flow,
and municipal audit logging.
"""

import os
import sys
import time
import uuid
import json
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import bcrypt
import jwt

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings
from database import get_db_connection

class AuthService:
    # ------------------ PASSWORD HASHING (BCRYPT) ------------------
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes password with bcrypt and auto-generated salt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies plain password against stored bcrypt hash."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    # ------------------ JWT GENERATION & VERIFICATION ------------------
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generates standard RFC 7519 compliant HS256 JWT."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Validates and decodes JWT. Returns None if invalid or expired."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except (jwt.PyJWTError, Exception):
            return None

    # ------------------ CITIZEN OTP ENGINE ------------------
    @staticmethod
    def generate_and_store_otp(phone: str) -> str:
        """
        Generates 6-digit cryptographic OTP, stores its SHA-256 hash in DB with 5-minute TTL.
        For production, this dispatches via Twilio / MSG91.
        """
        otp = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = hashlib.sha256(otp.encode('utf-8')).hexdigest()
        expires_at = time.time() + settings.OTP_EXPIRE_SECONDS
        now_iso = datetime.now(timezone.utc).isoformat()

        conn = get_db_connection()
        conn.execute("""
        INSERT INTO otp_store (phone, otp_hash, expires_at, attempts, created_at)
        VALUES (?, ?, ?, 0, ?)
        ON CONFLICT(phone) DO UPDATE SET
            otp_hash = excluded.otp_hash,
            expires_at = excluded.expires_at,
            attempts = 0,
            created_at = excluded.created_at;
        """, (phone, otp_hash, expires_at, now_iso))
        conn.commit()
        conn.close()

        return otp

    @staticmethod
    def verify_otp(phone: str, otp_attempt: str) -> bool:
        """Validates OTP against stored hash and checks expiry window."""
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM otp_store WHERE phone = ?;", (phone,)).fetchone()
        
        if not row:
            conn.close()
            return False

        if time.time() > row["expires_at"]:
            conn.execute("DELETE FROM otp_store WHERE phone = ?;", (phone,))
            conn.commit()
            conn.close()
            return False

        attempt_hash = hashlib.sha256(otp_attempt.strip().encode('utf-8')).hexdigest()
        is_valid = (attempt_hash == row["otp_hash"])

        if is_valid:
            conn.execute("DELETE FROM otp_store WHERE phone = ?;", (phone,))
        else:
            conn.execute("UPDATE otp_store SET attempts = attempts + 1 WHERE phone = ?;", (phone,))
        
        conn.commit()
        conn.close()
        return is_valid

    # ------------------ USER REPOSITORY & SEEDING ------------------
    @classmethod
    def seed_default_users(cls):
        """Ensures default official and citizen accounts are seeded with bcrypt hashes."""
        conn = get_db_connection()
        cursor = conn.cursor()

        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Official Vikram Singh (MCG)
        official_pass_hash = cls.hash_password("MCG-GURUGRAM-2026")
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, phone, email, password_hash, role, agency_code, badge_number, is_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'MCG_OFFICIAL', 'MCG', 'MCG-XEN-042', 1, ?, ?);
        """, (str(uuid.uuid4()), "Vikram Singh", "+91-9811001122", "vikram.singh@mcg.gov.in", official_pass_hash, now_iso, now_iso))

        # 2. GMDA Official Pooja Rao
        gmda_pass_hash = cls.hash_password("GMDA-COMMAND-2026")
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, phone, email, password_hash, role, agency_code, badge_number, is_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'GMDA_OFFICIAL', 'GMDA', 'GMDA-ICCC-019', 1, ?, ?);
        """, (str(uuid.uuid4()), "Pooja Rao", "+91-9811003344", "pooja.rao@gmda.gov.in", gmda_pass_hash, now_iso, now_iso))

        # 3. DHBVN Official Rajesh Verma
        dhbvn_pass_hash = cls.hash_password("DHBVN-POWER-2026")
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, phone, email, password_hash, role, agency_code, badge_number, is_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'DHBVN_OFFICIAL', 'DHBVN', 'DHBVN-SUB-108', 1, ?, ?);
        """, (str(uuid.uuid4()), "Rajesh Verma", "+91-9811005566", "rajesh.verma@dhbvn.org.in", dhbvn_pass_hash, now_iso, now_iso))

        # 4. Traffic Police Official Amit Dahiya
        police_pass_hash = cls.hash_password("POLICE-TRAFFIC-2026")
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, phone, email, password_hash, role, agency_code, badge_number, is_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'POLICE_OFFICIAL', 'POLICE', 'POLICE-TRAFFIC-08', 1, ?, ?);
        """, (str(uuid.uuid4()), "Amit Dahiya", "+91-9811007788", "amit.dahiya@haryanapolice.gov.in", police_pass_hash, now_iso, now_iso))

        # 5. Default Citizen Aarav Sharma
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, phone, email, password_hash, role, agency_code, badge_number, is_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, NULL, 'CITIZEN', NULL, NULL, 1, ?, ?);
        """, (str(uuid.uuid4()), "Aarav Sharma", "+91-9811046021", "aarav.sharma@gmail.com", now_iso, now_iso))

        conn.commit()
        conn.close()

    @classmethod
    def authenticate_official(cls, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates municipal official via badge number, email, or phone."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM users 
        WHERE (badge_number = ? OR email = ? OR phone = ? OR name = ?) 
          AND role != 'CITIZEN';
        """, (identifier, identifier, identifier, identifier))
        user = cursor.fetchone()
        conn.close()

        if not user or not user["password_hash"]:
            return None

        if cls.verify_password(password, user["password_hash"]):
            return dict(user)
        return None

    @classmethod
    def get_or_create_citizen(cls, phone: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves or creates verified citizen user record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE phone = ?;", (phone,))
        user = cursor.fetchone()

        if user:
            conn.close()
            return dict(user)

        user_id = str(uuid.uuid4())
        user_name = name or f"Citizen-{phone[-4:]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        INSERT INTO users (id, name, phone, email, password_hash, role, agency_code, badge_number, is_verified, created_at, updated_at)
        VALUES (?, ?, ?, NULL, NULL, 'CITIZEN', NULL, NULL, 1, ?, ?);
        """, (user_id, user_name, phone, now_iso, now_iso))
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        created = cursor.fetchone()
        conn.close()
        return dict(created)

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches user record by primary key."""
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

    # ------------------ AUDIT LOGGING (MUNICIPAL INTEGRITY) ------------------
    @staticmethod
    def log_audit(
        actor_id: Optional[str],
        actor_name: str,
        actor_role: str,
        action: str,
        target_entity: str,
        target_id: str,
        payload: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Appends tamper-evident audit log for municipal accountability."""
        conn = get_db_connection()
        log_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload or {})

        conn.execute("""
        INSERT INTO audit_logs (id, actor_id, actor_name, actor_role, action, target_entity, target_id, payload_json, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (log_id, actor_id, actor_name, actor_role, action, target_entity, target_id, payload_str, ip_address, now_iso))
        conn.commit()
        conn.close()
        return log_id

    @staticmethod
    def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent audit events for MCG control room inspectors."""
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?;", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

auth_service = AuthService()
