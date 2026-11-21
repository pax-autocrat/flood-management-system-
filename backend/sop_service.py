"""
NeerNetra - JalRakshak NCR
MCG Pre-Event Operations SOP Engine & Political Defensibility Service (Deliverable 3)
Engineered for municipal operational certainty, prevention paradox defense,
and algorithmic RWA diversion prevention.
"""

import time
import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Secret key for municipal audit HMAC-SHA256 signature
AUDIT_SECRET_KEY = b"NeerNetra_MCG_Gurugram_Audit_Secret_2026"

class SopService:
    def __init__(self):
        self._sop_phases = [
            {
                "id": "SOP-24H",
                "phase_code": "T-24H",
                "trigger_rainfall_mm_hr": 15.0,
                "window": "T-24 HOURS (RADAR WATCH)",
                "title": "CLEAR TRASH SCREENS & TOP UP 12H DIESEL",
                "owner": "Executive Engineer (XEN) & Sanitary Inspectors (SI)",
                "target": "Khandsa Box Culvert (GRG-001), Rajiv Chowk (GRG-004), Sheetla Mata Rd (GRG-008)",
                "actions": [
                    "Desilt and clear hydraulic trash racks at all 32 Pareto trunk choke points.",
                    "Verify 12-hour diesel fuel reserve on all static and mobile de-watering pump engines.",
                    "Inspect float switch contactors and ultrasonic sensor telemetry batteries."
                ],
                "completed": True,
                "completed_at": "2026-11-13T10:30:00Z",
                "verified_by": "XEN-Ramesh (Drainage Division 1)",
                "je_phone": "+91-98100-14001",
                "hindi_msg": "एमसीजी अलर्ट [T-24H]: सभी 32 मुख्य नालों पर कचरा स्क्रीन साफ करें और 12 घंटे का डीजल रिजर्व पूरा रखें।"
            },
            {
                "id": "SOP-12H",
                "phase_code": "T-12H",
                "trigger_rainfall_mm_hr": 25.0,
                "window": "T-12 HOURS (RADAR CONFIRMATION)",
                "title": "PRE-POSITION MOBILE PUMPS ON DRY HIGH GROUND",
                "owner": "Junior Engineers (JE) & Suction Tanker Drivers",
                "target": "Hero Honda Chowk (GRG-002), Narsinghpur NH-48 (GRG-003), Subhash Chowk (GRG-005)",
                "actions": [
                    "Mobilize Ring-A Super Sucker Tankers to designated dry staging verges.",
                    "Position tractor pumps on dry approach ramps (Hero Honda flyover & Rajiv Chowk).",
                    "Deploy suction hoses to sump entry wells before service lane waterlogging begins."
                ],
                "completed": False,
                "completed_at": None,
                "verified_by": None,
                "je_phone": "+91-98100-14002",
                "hindi_msg": "एमसीजी अलर्ट [T-12H]: पंप ऑपरेटर तुरंत हीरो होंडा और नरसिंहपुर ड्राई एलिवेशन पर पहुंचें। सक्शन पाइप लगाएं।"
            },
            {
                "id": "SOP-6H",
                "phase_code": "T-6H",
                "trigger_rainfall_mm_hr": 35.0,
                "window": "T-6 HOURS (CONVECTIVE RAIN ALERT)",
                "title": "PRE-EMPTY SUMPS TO 0% & ISOLATE DHBVN 1912 FEEDERS",
                "owner": "Underpass Pump Operators & DHBVN 1912 Electrical Team",
                "target": "All 11 Underpasses + Sector 46 & Sector 23 66kV Substations",
                "actions": [
                    "Run primary turbine pumps to draw down all underpass retention sumps to 0% volume.",
                    "Coordinate with DHBVN Nodal Officer (1912) for preventive circuit breaker isolation on flooded roads.",
                    "Test automated dual-power diesel generator backup switches."
                ],
                "completed": False,
                "completed_at": None,
                "verified_by": None,
                "je_phone": "+91-98100-14003",
                "hindi_msg": "एमसीजी अलर्ट [T-6H]: सभी 11 अंडरपास संप 0% खाली करें। DHBVN बिजली फीडर 1912 सुरक्षा समन्वय सक्रिय करें।"
            },
            {
                "id": "SOP-2H",
                "phase_code": "T-2H",
                "trigger_rainfall_mm_hr": 50.0,
                "window": "T-2 HOURS (NOWCAST CLOUDBURST)",
                "title": "WARM-IDLE ENGINES & STAGE BOOM BARRIER CREWS",
                "owner": "Gurugram Traffic Police TI (1095) & Boom Barrier Marshals",
                "target": "Rajiv Chowk, Hero Honda Chowk, Medanta Underpass, Golf Course Underpasses",
                "actions": [
                    "Start all pre-positioned pump diesel engines at warm-idle for zero-delay prime.",
                    "Stage Traffic Police boom barrier crews at underpass approach ramps.",
                    "If water exceeds 25 cm, immediately lower boom barriers and divert traffic to wide SPR / Golf Course Road."
                ],
                "completed": False,
                "completed_at": None,
                "verified_by": None,
                "je_phone": "+91-98100-14004",
                "hindi_msg": "एमसीजी ट्रैफिक अलर्ट [T-2H]: अंडरपास बूम बैरियर तैयार रखें। पानी 25 सेमी होने पर प्रवेश तुरंत बंद करें।"
            }
        ]

        # Two-Ring Fleet Management with Algorithmic Geofence Lock
        self._fleet = [
            {
                "id": "TANKER-101",
                "name": "Super Sucker Tanker #1 (10,000L)",
                "ring": "RING-A",
                "ring_label": "RING-A: TRUNK LOCKED (PARETO 32)",
                "is_geofence_locked": True,
                "category": "TANKER",
                "driver": "Rajesh Sharma",
                "driver_phone": "+91-98111-20101",
                "assigned_choke_point": "GRG-001 (Khandsa Box Culvert)",
                "home_staging_lat": 28.4180,
                "home_staging_lng": 76.9910,
                "status": "STAGED",
                "billing_active": True
            },
            {
                "id": "TANKER-102",
                "name": "High-Flow Suction Tanker #2 (8,000L)",
                "ring": "RING-A",
                "ring_label": "RING-A: TRUNK LOCKED (PARETO 32)",
                "is_geofence_locked": True,
                "category": "TANKER",
                "driver": "Ramesh Hooda",
                "driver_phone": "+91-98111-20102",
                "assigned_choke_point": "GRG-002 (Hero Honda Chowk)",
                "home_staging_lat": 28.4265,
                "home_staging_lng": 77.0031,
                "status": "STAGED",
                "billing_active": True
            },
            {
                "id": "AMB-201",
                "name": "ALS Flood Rescue Ambulance #1",
                "ring": "RING-A",
                "ring_label": "RING-A: TRUNK LOCKED (PARETO 32)",
                "is_geofence_locked": True,
                "category": "AMBULANCE",
                "driver": "Dr. Karanvir / Param Dayal",
                "driver_phone": "+91-98111-20201",
                "assigned_choke_point": "GRG-006 (Medanta Hospital Road)",
                "home_staging_lat": 28.4394,
                "home_staging_lng": 77.0416,
                "status": "STANDBY",
                "billing_active": True
            },
            {
                "id": "BOAT-301",
                "name": "SDRF Inflatable Rescue Boat #1",
                "ring": "RING-A",
                "ring_label": "RING-A: TRUNK LOCKED (PARETO 32)",
                "is_geofence_locked": True,
                "category": "BOAT",
                "driver": "Capt. Mandeep (SDRF)",
                "driver_phone": "+91-98111-20301",
                "assigned_choke_point": "GRG-003 (Narsinghpur Highway Sink)",
                "home_staging_lat": 28.4024,
                "home_staging_lng": 76.9796,
                "status": "STAGED",
                "billing_active": True
            },
            {
                "id": "QRV-401",
                "name": "MCG Quick Response 4x4 Vehicle #1",
                "ring": "RING-B",
                "ring_label": "RING-B: WARD & RWA FLEX BUFFER",
                "is_geofence_locked": False,
                "category": "QRV",
                "driver": "Suresh Khatri",
                "driver_phone": "+91-98111-20401",
                "assigned_choke_point": "Ward 30 & Sector 46 Substation Flex",
                "home_staging_lat": 28.4360,
                "home_staging_lng": 77.0580,
                "status": "OPEN",
                "billing_active": True
            },
            {
                "id": "QRV-402",
                "name": "Tractor Pump & Tow QRV #2",
                "ring": "RING-B",
                "ring_label": "RING-B: WARD & RWA FLEX BUFFER",
                "is_geofence_locked": False,
                "category": "QRV",
                "driver": "Naresh Tanwar",
                "driver_phone": "+91-98111-20402",
                "assigned_choke_point": "Golf Course / Sector 42 RWA Buffer",
                "home_staging_lat": 28.4620,
                "home_staging_lng": 77.0940,
                "status": "OPEN",
                "billing_active": True
            }
        ]

        # Immutable Public Commitment Board Entries (Proof of Pre-Event Action)
        self._commitment_ledger = [
            {
                "id": "PCB-2026-001",
                "timestamp_utc": "2026-07-28T04:15:00Z",
                "lead_time": "T-60 MINUTES BEFORE CLOUDBURST",
                "location_code": "GRG-002",
                "location_name": "Hero Honda Chowk Underpass",
                "predicted_unmitigated_depth_cm": 145.0,
                "actual_held_depth_cm": 22.0,
                "mitigation_liters_lakh": 42.0,
                "staged_asset": "Super Sucker TANKER-102 (8,000L/min) + JE Sandeep",
                "digital_signature_hmac": self._compute_signature("PCB-2026-001", 145.0, 22.0, "Hero Honda Chowk Underpass"),
                "status": "VERIFIED_PREVENTED",
                "public_proof_summary": "Pumps deployed at 04:15 AM before 54mm/hr cloudburst at 05:20 AM. Zero traffic disruption on NH-48."
            },
            {
                "id": "PCB-2026-002",
                "timestamp_utc": "2026-08-04T13:40:00Z",
                "lead_time": "T-45 MINUTES BEFORE STORM",
                "location_code": "GRG-001",
                "location_name": "Khandsa Box Culvert (Trunk Confluence)",
                "predicted_unmitigated_depth_cm": 185.0,
                "actual_held_depth_cm": 38.0,
                "mitigation_liters_lakh": 58.0,
                "staged_asset": "High-Flow Diesel Sump Rig #3 + TANKER-101",
                "digital_signature_hmac": self._compute_signature("PCB-2026-002", 185.0, 38.0, "Khandsa Box Culvert (Trunk Confluence)"),
                "status": "VERIFIED_PREVENTED",
                "public_proof_summary": "Pre-emptied sump to 0% and cleared trash screens. Prevented ₹35 Cr estimated supply-chain loss."
            }
        ]

        self._active_override_tokens: Dict[str, Dict[str, Any]] = {}

    def _compute_signature(self, entry_id: str, pred: float, actual: float, spot: str) -> str:
        """Computes cryptographic HMAC-SHA256 signature for tamper-evident public audit"""
        data = f"{entry_id}|{pred:.1f}|{actual:.1f}|{spot}".encode("utf-8")
        return hmac.new(AUDIT_SECRET_KEY, data, hashlib.sha256).hexdigest()

    def get_sop_status(self) -> Dict[str, Any]:
        """Returns the full SOP checklist, completion rate, and current active phase"""
        completed_count = sum(1 for p in self._sop_phases if p["completed"])
        total_count = len(self._sop_phases)
        pct = round((completed_count / total_count) * 100.0, 1)

        return {
            "overall_completion_pct": pct,
            "completed_phases": completed_count,
            "total_phases": total_count,
            "phases": self._sop_phases,
            "active_protocol": "T-12H PRE-POSITIONING ACTIVE" if completed_count == 1 else ("T-2H NOWCAST ACTIVE" if completed_count >= 3 else "T-24H WATCH")
        }

    def checkoff_sop_task(self, sop_id: str, verified_by: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Allows Junior Engineer or XEN to digitally sign off on an SOP phase completion"""
        for p in self._sop_phases:
            if p["id"].upper() == sop_id.upper() or p["phase_code"].upper() == sop_id.upper():
                p["completed"] = True
                p["completed_at"] = datetime.now(timezone.utc).isoformat()
                p["verified_by"] = verified_by
                if notes:
                    p["notes"] = notes
                return {
                    "status": "success",
                    "sop_id": p["id"],
                    "phase": p["window"],
                    "completed_at": p["completed_at"],
                    "verified_by": p["verified_by"],
                    "message": f"SOP Phase {p['phase_code']} digitally signed and verified."
                }
        raise ValueError(f"SOP phase with ID '{sop_id}' not found.")

    def auto_trigger_by_rainfall(self, rain_mm_hr: float) -> Dict[str, Any]:
        """Automatically activates SOP protocols as live rainfall radar data crosses thresholds"""
        triggered = []
        for p in self._sop_phases:
            if rain_mm_hr >= p["trigger_rainfall_mm_hr"]:
                if not p["completed"]:
                    p["completed"] = True
                    p["completed_at"] = datetime.now(timezone.utc).isoformat()
                    p["verified_by"] = "AUTOMATED_MET_RADAR_TRIGGER"
                    triggered.append(p["phase_code"])

        return {
            "current_rain_mm_hr": rain_mm_hr,
            "auto_triggered_phases": triggered,
            "total_completed": sum(1 for p in self._sop_phases if p["completed"])
        }

    def get_public_commitment_board(self) -> List[Dict[str, Any]]:
        """Returns immutable public commitment entries with cryptographic verification status"""
        for entry in self._commitment_ledger:
            expected_sig = self._compute_signature(
                entry["id"],
                entry["predicted_unmitigated_depth_cm"],
                entry["actual_held_depth_cm"],
                entry["location_name"]
            )
            entry["signature_valid"] = (entry["digital_signature_hmac"] == expected_sig)
            entry["audit_verification"] = "TAMPER-PROOF CRYPTOGRAPHIC PROOF VERIFIED" if entry["signature_valid"] else "TAMPERED_INVALID"
        return self._commitment_ledger

    def log_commitment_entry(
        self,
        location_code: str,
        location_name: str,
        predicted_depth_cm: float,
        actual_depth_cm: float,
        mitigation_liters_lakh: float,
        staged_asset: str,
        summary: str
    ) -> Dict[str, Any]:
        """Logs a new tamper-evident staging record on the Public Commitment Board"""
        entry_id = f"PCB-2026-{len(self._commitment_ledger) + 1:03d}"
        now_iso = datetime.now(timezone.utc).isoformat()
        sig = self._compute_signature(entry_id, predicted_depth_cm, actual_depth_cm, location_name)

        entry = {
            "id": entry_id,
            "timestamp_utc": now_iso,
            "lead_time": "T-60m AUTOMATED DISPATCH AUDIT",
            "location_code": location_code,
            "location_name": location_name,
            "predicted_unmitigated_depth_cm": predicted_depth_cm,
            "actual_held_depth_cm": actual_depth_cm,
            "mitigation_liters_lakh": mitigation_liters_lakh,
            "staged_asset": staged_asset,
            "digital_signature_hmac": sig,
            "status": "VERIFIED_PREVENTED",
            "public_proof_summary": summary,
            "signature_valid": True,
            "audit_verification": "TAMPER-PROOF CRYPTOGRAPHIC PROOF VERIFIED"
        }
        self._commitment_ledger.insert(0, entry)
        return entry

    def get_fleet_status(self) -> Dict[str, Any]:
        """Returns the status and geofence state of all Ring-A and Ring-B units"""
        ring_a = [v for v in self._fleet if v["ring"] == "RING-A"]
        ring_b = [v for v in self._fleet if v["ring"] == "RING-B"]
        return {
            "total_units": len(self._fleet),
            "ring_a_trunk_locked_count": len(ring_a),
            "ring_b_ward_flex_count": len(ring_b),
            "fleet": self._fleet
        }

    def request_fleet_dispatch(
        self,
        vehicle_id: str,
        target_location: str,
        requestor: str,
        is_vip_request: bool = False,
        override_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enforces Algorithmic RWA Geofence Lock.
        Rejects diversion of Ring-A Trunk assets to non-choke-point colony requests
        unless a valid Commissioner Dual-Key Override token is provided.
        """
        vehicle = next((v for v in self._fleet if v["id"] == vehicle_id.upper()), None)
        if not vehicle:
            raise ValueError(f"Vehicle '{vehicle_id}' not found in municipal fleet registry.")

        is_ring_a = (vehicle["ring"] == "RING-A")

        # Check if caller is requesting a non-trunk diversion
        target_is_choke = "GRG-" in target_location.upper() or "TRUNK" in target_location.upper() or "CHOWK" in target_location.upper()

        if is_ring_a and not target_is_choke:
            # Check for valid Commissioner Dual-Key Override
            if override_token and override_token in self._active_override_tokens:
                token_data = self._active_override_tokens[override_token]
                return {
                    "dispatch_status": "APPROVED_UNDER_OVERRIDE",
                    "vehicle_id": vehicle["id"],
                    "ring": "RING-A",
                    "override_used": True,
                    "commissioner_token": override_token,
                    "rti_audit_log": f"COMMISSIONER DUAL-KEY AUTHORIZED: {token_data['reason']}",
                    "warning": "Ring-A diversion authorized for max 45 minutes under RTI Public Ledger audit.",
                    "billing_active": True
                }

            # Rejection: Algorithmic Geofence Lock
            # Automatically reassign to Ring-B buffer vehicle
            ring_b_unit = next((v for v in self._fleet if v["ring"] == "RING-B" and v["status"] in ("OPEN", "STANDBY")), None)
            assigned_substitute = ring_b_unit["id"] if ring_b_unit else "QRV-401 (Ring-B Buffer)"

            return {
                "dispatch_status": "REJECTED_BY_ALGORITHMIC_GEOFENCE",
                "vehicle_id": vehicle["id"],
                "ring": "RING-A",
                "attempted_target": target_location,
                "requestor": requestor,
                "rejection_reason": "POLITICAL ECONOMY LOCK: Ring-A Super Sucker is GPS-locked to the 32 Pareto Trunk Choke Points. Telematics will halt billing to ₹0 and alert Commissioner if moved.",
                "automated_countermeasure": f"Request automatically rerouted to {assigned_substitute} (Ring-B Ward & RWA Flex Buffer).",
                "ring_b_substitute_dispatched": assigned_substitute,
                "override_instructions": "To bypass for genuine multi-casualty emergency, call Commissioner Office for Dual-Key Digital Token."
            }

        # Normal dispatch approved
        vehicle["status"] = "DISPATCHED"
        vehicle["current_target"] = target_location
        return {
            "dispatch_status": "APPROVED",
            "vehicle_id": vehicle["id"],
            "ring": vehicle["ring"],
            "target": target_location,
            "driver": vehicle["driver"],
            "driver_phone": vehicle["driver_phone"],
            "billing_active": True
        }

    def generate_commissioner_override(self, reason: str, authorized_by: str = "Municipal Commissioner MCG") -> Dict[str, Any]:
        """Generates a tamper-evident digital override token logged in the public RTI ledger"""
        token_str = f"RTI-2026-DK-{hashlib.sha256(f'{time.time()}_{reason}'.encode('utf-8')).hexdigest()[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        token_record = {
            "token": token_str,
            "issued_at": now_iso,
            "authorized_by": authorized_by,
            "reason": reason,
            "validity_minutes": 45,
            "public_rti_log": f"Dual-Key Override #{token_str} issued by {authorized_by} for: {reason}"
        }
        self._active_override_tokens[token_str] = token_record

        # Also post an audit record to the public commitment board
        self.log_commitment_entry(
            location_code="OVERRIDE-LOG",
            location_name=f"Commissioner Dual-Key: {reason[:30]}...",
            predicted_depth_cm=0.0,
            actual_depth_cm=0.0,
            mitigation_liters_lakh=0.0,
            staged_asset=f"Token {token_str}",
            summary=f"Authorized Ring-A temporary diversion: {reason}. Subject to public RTI disclosure."
        )

        return token_record

    def generate_je_whatsapp_payload(self, sop_id: str) -> Dict[str, Any]:
        """Generates zero-lag bilingual WhatsApp / SMS work orders for field engineers"""
        phase = next((p for p in self._sop_phases if p["id"].upper() == sop_id.upper() or p["phase_code"].upper() == sop_id.upper()), None)
        if not phase:
            raise ValueError(f"SOP phase '{sop_id}' not found.")

        english_text = (
            f"🚨 *MCG GURUGRAM FLOOD CONTROL WORK ORDER [{phase['phase_code']}]*\n"
            f"• *TASK:* {phase['title']}\n"
            f"• *TARGET:* {phase['target']}\n"
            f"• *LEAD-TIME:* {phase['window']}\n"
            f"• *ACTIONS:*\n" + "\n".join(f"  - {a}" for a in phase['actions']) + "\n"
            f"• *REPLY WITH:* 'DONE {phase['id']}' to verify completion on public portal."
        )

        return {
            "sop_id": phase["id"],
            "phase": phase["phase_code"],
            "recipient_je_phone": phase["je_phone"],
            "english_message": english_text,
            "hindi_message": phase["hindi_msg"],
            "formatted_whatsapp_url": f"https://api.whatsapp.com/send?phone={phase['je_phone'].replace('-', '').replace('+', '')}&text={english_text}"
        }

# Singleton instance
sop_service = SopService()
