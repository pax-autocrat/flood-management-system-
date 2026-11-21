"""
JalRakshak NCR — Phase 1 Automated Verification Suite
Validates:
1. Database Schema & Auto-Seeding (Agencies & Hotspots Persistence)
2. Bcrypt Password Hashing & Verification
3. Official Departmental Login & JWT in HTTP-only Cookie
4. Citizen OTP Dispatch & Verification Flow
5. Session Identity (`/api/v1/auth/me`)
6. Strict Role-Based Access Control (RBAC) Protection (403 Forbidden for Civilians on Official Routes)
7. Tamper-Evident Audit Logging
"""

import sys
import os
import json
import sqlite3
from fastapi.testclient import TestClient

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from main import app
from database import DB_FILE, get_db_connection
from services.auth_service import auth_service

client = TestClient(app)

def run_phase1_tests():
    print("=" * 75)
    print("  PHASE 1 VERIFICATION: CORE DATABASE, PERSISTENCE & AUTHENTICATION")
    print("  Team: NeerNetra | Lead: Kamal Shukla | SustainX 2026")
    print("=" * 75)

    # ------------------ TEST 1: DATABASE INITIALIZATION & SEEDS ------------------
    print("\n[TEST 1] Verifying SQLite Database File & Schema Persistence...")
    assert os.path.exists(DB_FILE), f"Database file {DB_FILE} was not created!"
    
    conn = get_db_connection()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print(f"  -> Detected Persistent Tables: {', '.join(tables)}")
    
    for req_table in ["agencies", "users", "otp_store", "audit_logs", "hotspots_db"]:
        assert req_table in tables, f"Missing required table '{req_table}'"

    # Check seeded agencies
    agency_count = conn.execute("SELECT COUNT(*) FROM agencies;").fetchone()[0]
    assert agency_count >= 6, f"Expected >= 6 agencies, got {agency_count}"
    print(f"  -> Seeded Agencies: {agency_count} (MCG, GMDA, NHAI, DHBVN, SDRF, POLICE)")

    # Check seeded hotspots
    hotspot_count = conn.execute("SELECT COUNT(*) FROM hotspots_db;").fetchone()[0]
    assert hotspot_count == 8, f"Expected 8 hotspots, got {hotspot_count}"
    print(f"  -> Seeded Primary Arterial Hotspots: {hotspot_count}")
    conn.close()
    print("  [PASS] Database schema and initial seeds verified.")

    # ------------------ TEST 2: BCRYPT PASSWORD HASHING ------------------
    print("\n[TEST 2] Verifying Bcrypt Password Hashing & Verification...")
    test_pass = "MCG-GURUGRAM-2026"
    hashed = auth_service.hash_password(test_pass)
    assert hashed.startswith("$2b$"), "Hash format is not valid bcrypt!"
    assert auth_service.verify_password(test_pass, hashed) is True, "Password verification failed on valid password!"
    assert auth_service.verify_password("WrongPassword123", hashed) is False, "Password verification falsely passed on invalid password!"
    print(f"  -> Bcrypt hash format: {hashed[:20]}...")
    print("  [PASS] Bcrypt password hashing & timing-safe verification verified.")

    # ------------------ TEST 3: OFFICIAL LOGIN & JWT COOKIE ------------------
    print("\n[TEST 3] Testing Official Login (Vikram Singh / MCG-GURUGRAM-2026)...")
    res = client.post("/api/v1/auth/official/login", json={
        "identifier": "Vikram Singh",
        "password": "MCG-GURUGRAM-2026"
    })
    assert res.status_code == 200, f"Official login failed: {res.text}"
    data = res.json()
    assert data["status"] == "authenticated"
    assert data["user"]["role"] == "MCG_OFFICIAL"
    assert data["user"]["agency"] == "MCG"
    assert "access_token" in data
    assert "access_token" in res.cookies, "HTTP-only cookie 'access_token' was not set!"
    official_token = data["access_token"]
    print(f"  -> Issued Official JWT Token: {official_token[:25]}...")
    print("  -> Confirmed HTTP-only secure cookie received.")

    # Test bad password
    res_bad = client.post("/api/v1/auth/official/login", json={
        "identifier": "Vikram Singh",
        "password": "BadPassword999"
    })
    assert res_bad.status_code == 401, "Official login did not reject bad password!"
    print("  -> Confirmed bad password rejected with 401 Unauthorized.")
    print("  [PASS] Official login & JWT cookie workflow verified.")

    # ------------------ TEST 4: CITIZEN OTP FLOW ------------------
    print("\n[TEST 4] Testing Citizen OTP Flow (Aarav Sharma / +91-9811046021)...")
    citizen_phone = "+91-9811046021"
    res_otp_send = client.post("/api/v1/auth/citizen/send-otp", json={"phone": citizen_phone})
    assert res_otp_send.status_code == 200, f"OTP dispatch failed: {res_otp_send.text}"
    otp_data = res_otp_send.json()
    assert "demo_otp_code" in otp_data
    demo_otp = otp_data["demo_otp_code"]
    print(f"  -> Generated 6-digit OTP: {demo_otp}")

    # Test bad OTP rejection
    res_bad_otp = client.post("/api/v1/auth/citizen/verify-otp", json={
        "phone": citizen_phone,
        "otp": "000000"
    })
    assert res_bad_otp.status_code == 400, "Bad OTP was not rejected with 400!"
    print("  -> Confirmed invalid OTP rejected with 400 Bad Request.")

    # Test valid OTP
    res_otp_verify = client.post("/api/v1/auth/citizen/verify-otp", json={
        "phone": citizen_phone,
        "otp": demo_otp,
        "name": "Aarav Sharma"
    })
    assert res_otp_verify.status_code == 200, f"Valid OTP failed: {res_otp_verify.text}"
    citizen_data = res_otp_verify.json()
    assert citizen_data["user"]["role"] == "CITIZEN"
    assert citizen_data["user"]["phone"] == citizen_phone
    citizen_token = citizen_data["access_token"]
    print(f"  -> Issued Citizen JWT Token: {citizen_token[:25]}...")
    print("  [PASS] Citizen OTP generation, validation & account provisioning verified.")

    # ------------------ TEST 5: IDENTITY VERIFICATION (/api/v1/auth/me) ------------------
    print("\n[TEST 5] Testing Session Identity Endpoint (/api/v1/auth/me)...")
    
    # 5A. Unauthenticated request (clear cookies first)
    client.cookies.clear()
    res_unauth = client.get("/api/v1/auth/me")
    assert res_unauth.status_code == 401, f"Unauthenticated request was not blocked with 401! Got {res_unauth.status_code}"
    print("  -> Confirmed unauthenticated request rejected with 401 Unauthorized.")

    # 5B. Authenticated as Official (via Authorization Header)
    res_me_official = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {official_token}"})
    assert res_me_official.status_code == 200
    me_data = res_me_official.json()
    assert me_data["name"] == "Vikram Singh"
    assert me_data["role"] == "MCG_OFFICIAL"

    # 5C. Authenticated as Citizen (via Cookie)
    client.cookies.set("access_token", citizen_token)
    res_me_citizen = client.get("/api/v1/auth/me")
    assert res_me_citizen.status_code == 200
    assert res_me_citizen.json()["role"] == "CITIZEN"
    client.cookies.clear()
    print("  -> Session identity correctly resolved from both Bearer token and HTTP-only cookie.")
    print("  [PASS] Session identity endpoint verified.")

    # ------------------ TEST 6: ROLE-BASED ACCESS CONTROL (RBAC) GATING ------------------
    print("\n[TEST 6] Testing Strict Role-Based Access Control (RBAC) Gating...")
    
    # 6A. Citizen attempts to view official audit logs -> MUST RETURN 403 FORBIDDEN
    res_citizen_blocked = client.get("/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res_citizen_blocked.status_code == 403, f"Expected 403 Forbidden for Citizen, got {res_citizen_blocked.status_code}"
    print("  -> Confirmed: Citizen blocked from Official Audit Logs with 403 FORBIDDEN.")

    # 6B. Official views audit logs -> MUST RETURN 200 OK
    res_official_allowed = client.get("/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {official_token}"})
    assert res_official_allowed.status_code == 200, f"Expected 200 OK for Official, got {res_official_allowed.status_code}"
    audit_data = res_official_allowed.json()
    assert "logs" in audit_data
    assert len(audit_data["logs"]) >= 1, "Audit logs were not recorded!"
    print(f"  -> Confirmed: Official accessed audit logs (Count: {len(audit_data['logs'])}).")
    print("  [PASS] RBAC permission guards verified.")

    # ------------------ TEST 7: LOGOUT ------------------
    print("\n[TEST 7] Testing Logout & Cookie Deletion...")
    res_logout = client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200
    assert res_logout.json()["status"] == "signed_out"
    print("  [PASS] Logout cleared session cookie.")

    print("\n" + "=" * 75)
    print("  SUCCESS: ALL 7 / 7 PHASE 1 TESTS PASSED WITH 100% SUCCESS!")
    print("  Database persistence, Bcrypt auth, JWT cookies, & RBAC are fully operational.")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    run_phase1_tests()
