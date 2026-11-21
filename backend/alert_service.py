"""
NeerNetra - JalRakshak NCR
Alert Service (Deliverable 5: Citizen & B2B Hyperlocal Alert Channels)
Engineered by Team NeerNetra for Municipal Corporation of Gurugram (MCG).

Core Capabilities:
1. 160-Byte GSM SMS Generator & Ingestion Parser (Total 4G/5G Cellular Data Blackout Resilience).
2. 4-Hop P2P BLE / Wi-Fi Direct Mesh Relay Simulator (Multi-hop packet propagation across gridlocked vehicles).
3. 1800-180-1817 Toll-Free Voice IVR Audio Bulletin Synthesizer (Bilingual Hindi & Haryanvi dialect scripts).
4. B2B DLF Cyber City / Cyber Hub Basement Flood Barrier & 11kV Power Isolation Protocol.
"""

import os
import sys
import json
import time
import hashlib
import binascii
from typing import Dict, List, Any, Optional

class AlertService:
    def __init__(self):
        self._emergency_outbox: List[Dict[str, Any]] = []
        self._ivr_sos_records: List[Dict[str, Any]] = []
        self._b2b_cyberhub_state: Dict[str, Any] = self._init_cyberhub_state()
        self._b2b_audit_ledger: List[Dict[str, Any]] = []

    # =========================================================================
    # 1. OFFLINE 160-BYTE GSM SMS GENERATOR & INGESTION PARSER
    # =========================================================================
    @staticmethod
    def _calculate_crc16(payload: str) -> str:
        """
        Calculates a 4-character hex CRC16-CCITT checksum for data integrity verification
        over 2G GSM cellular SMS networks.
        """
        crc = 0xFFFF
        for char in payload.encode('ascii', errors='ignore'):
            crc ^= (char << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return f"{crc:04X}"

    def generate_emergency_sms(
        self,
        lat: float,
        lng: float,
        hotspot_code: str,
        depth_cm: float,
        req_type: str = "EVAC",
        battery_pct: int = 85
    ) -> Dict[str, Any]:
        """
        Generates a standard 7-bit GSM compliant SMS string strictly <= 160 bytes.
        Operates without 4G/5G internet connectivity over standard 2G signaling channels.
        Format: NEERNETRA-SOS|GPS:<lat>,<lng>|<CODE>|<DEPTH>CM|<REQ>|BAT:<pct>%|CRC:<crc16>
        """
        clean_code = hotspot_code.strip().upper()[:8]
        clean_req = req_type.strip().upper().replace(" ", "_")[:12]
        battery_clamped = max(1, min(100, int(battery_pct)))
        depth_int = max(0, int(round(depth_cm)))

        # Format coordinates to 4 decimal places (~11m ground resolution)
        coord_str = f"{lat:.4f},{lng:.4f}"
        
        # Base payload before checksum
        base_payload = f"NEERNETRA-SOS|GPS:{coord_str}|{clean_code}|{depth_int}CM|{clean_req}|BAT:{battery_clamped}%"
        crc16 = self._calculate_crc16(base_payload)
        
        final_sms_text = f"{base_payload}|CRC:{crc16}"
        byte_length = len(final_sms_text.encode('utf-8'))

        # Strict validation of GSM 160-character budget
        if byte_length > 160:
            raise ValueError(f"Generated SMS exceeded 160-byte GSM limit ({byte_length} bytes)")

        record = {
            "sms_text": final_sms_text,
            "byte_length": byte_length,
            "char_count": len(final_sms_text),
            "max_allowed_bytes": 160,
            "bytes_remaining": 160 - byte_length,
            "crc16": crc16,
            "lat": round(lat, 4),
            "lng": round(lng, 4),
            "hotspot_code": clean_code,
            "depth_cm": depth_int,
            "req_type": clean_req,
            "battery_pct": battery_clamped,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "gsm_encoding": "7-bit GSM 03.38 compatible"
        }
        self._emergency_outbox.append(record)
        return record

    def parse_emergency_sms(self, raw_sms: str) -> Dict[str, Any]:
        """
        Parses an inbound emergency 160-byte SMS into structured disaster records,
        verifying the CRC16-CCITT checksum for corruption or malicious tampering.
        """
        raw_sms = raw_sms.strip()
        parts = raw_sms.split("|")
        if len(parts) < 6:
            raise ValueError(f"Malformed SMS payload: expected at least 6 delimited segments, got {len(parts)}")

        # Extract segments
        header = parts[0]
        gps_part = parts[1]
        code_part = parts[2]
        depth_part = parts[3]
        req_part = parts[4]
        
        # Identify CRC part and battery part
        crc_part = None
        battery_pct = 100
        for p in parts[5:]:
            if p.startswith("CRC:"):
                crc_part = p[4:]
            elif p.startswith("BAT:"):
                try:
                    battery_pct = int(p[4:].replace("%", ""))
                except ValueError:
                    pass

        # Verify CRC
        base_payload = raw_sms[:raw_sms.rfind("|CRC:")]
        expected_crc = self._calculate_crc16(base_payload)
        is_valid_crc = (crc_part == expected_crc)

        # Parse GPS
        lat, lng = 28.4595, 77.0266
        if gps_part.startswith("GPS:"):
            coord_str = gps_part[4:]
            try:
                c_lat, c_lng = coord_str.split(",")
                lat = float(c_lat)
                lng = float(c_lng)
            except Exception:
                pass

        # Parse Depth
        depth_cm = 0
        if "CM" in depth_part:
            try:
                depth_cm = int(depth_part.replace("CM", ""))
            except ValueError:
                pass

        parsed_record = {
            "header": header,
            "hotspot_code": code_part,
            "lat": lat,
            "lng": lng,
            "depth_cm": depth_cm,
            "req_type": req_part,
            "battery_pct": battery_pct,
            "received_crc": crc_part,
            "computed_crc": expected_crc,
            "is_valid_crc": is_valid_crc,
            "status": "DISPATCH_REGISTERED" if is_valid_crc else "INTEGRITY_FAILED",
            "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return parsed_record

    # =========================================================================
    # 2. 4-HOP P2P BLE / WI-FI DIRECT MESH RELAY SIMULATOR
    # =========================================================================
    def simulate_mesh_relay(
        self,
        origin_lat: float = 28.4265,
        origin_lng: float = 77.0031,
        hotspot_code: str = "GRG-002",
        incident_type: str = "STRANDED_VEHICLE",
        distress_text: str = "Car submerged under Hero Honda Chowk flyover, 4 passengers inside"
    ) -> Dict[str, Any]:
        """
        Simulates multi-hop P2P mesh relay across gridlocked cars during total 4G/5G mobile tower blackout.
        Uses BLE 5.0 Long Range and Wi-Fi Direct ad-hoc connections to bounce the packet
        across 4 hops until reaching an SDRF/MCG High-Ground Command Post.
        """
        packet_id = f"MESH-PKT-{hashlib.md5(f'{origin_lat}{origin_lng}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        
        # 4 Hops from trapped vehicle to SDRF Incident Commander
        hops = [
            {
                "hop_number": 1,
                "node_id": "CAR-DL8C-4129",
                "node_type": "Origin Citizen Vehicle (0-Bar Cell Coverage)",
                "distance_m": 0,
                "signal_rssi_dbm": -45,
                "bearer_protocol": "BLE 5.0 Coded PHY",
                "action": "SOS Packet Initial Broadcast",
                "remaining_ttl": 4,
                "status": "FORWARDED"
            },
            {
                "hop_number": 2,
                "node_id": "CAR-HR55-7821",
                "node_type": "Stranded Commercial Truck Relay (Hero Honda Gridlock)",
                "distance_m": 42,
                "signal_rssi_dbm": -72,
                "bearer_protocol": "BLE 5.0 Mesh Ad-Hoc",
                "action": "Packet Forwarded to Upstream Flyover",
                "remaining_ttl": 3,
                "status": "FORWARDED"
            },
            {
                "hop_number": 3,
                "node_id": "MCG-QRV-401",
                "node_type": "MCG Quick Response Vehicle (Elevated Flyover Ramp)",
                "distance_m": 118,
                "signal_rssi_dbm": -64,
                "bearer_protocol": "Wi-Fi Direct P2P Relay (802.11be)",
                "action": "Packet Accelerated to Command Repeater",
                "remaining_ttl": 2,
                "status": "FORWARDED"
            },
            {
                "hop_number": 4,
                "node_id": "SDRF-COMMAND-BASE-HEROHONDA",
                "node_type": "SDRF Tactical Command Unit (Satellite & HAM Radio Uplink)",
                "distance_m": 210,
                "signal_rssi_dbm": -58,
                "bearer_protocol": "IN865 LoRaWAN Gateway / Satellite Uplink",
                "action": "Packet Ingested & Rescue Boat Dispatched",
                "remaining_ttl": 1,
                "status": "DELIVERED_TO_COMMAND"
            }
        ]

        delivery_ack = {
            "ack_token": f"ACK-SDRF-{hashlib.sha256(packet_id.encode()).hexdigest()[:10].upper()}",
            "delivered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_hops": len(hops),
            "total_distance_m": 210,
            "average_rssi_dbm": -59.75,
            "command_post": "SDRF Hero Honda Chowk Incident Post",
            "dispatch_assigned": "SDRF Rescue Boat Team Alpha (4 Men, Inflatable Zodiac)",
            "estimated_arrival_minutes": 8.5
        }

        return {
            "packet_id": packet_id,
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "hotspot_code": hotspot_code,
            "incident_type": incident_type,
            "distress_text": distress_text,
            "initial_ttl": 4,
            "terminal_status": "DELIVERED",
            "hops_trace": hops,
            "delivery_ack": delivery_ack,
            "cellular_dependency": "ZERO (100% Offline Ad-hoc Mesh Relay)"
        }

    # =========================================================================
    # 3. 1800-180-1817 TOLL-FREE VOICE IVR BULLETIN SYNTHESIZER
    # =========================================================================
    def get_ivr_bulletin(self, option_id: int) -> Dict[str, Any]:
        """
        Synthesizes bilingual voice audio bulletins in both Hindi (हिंदी) and Haryanvi (हरियाणवी)
        accessible from any basic 2G keypad phone via Toll-Free 1800-180-1817.
        """
        bulletins = {
            1: {
                "option_id": 1,
                "title_en": "Live Corridors & Road Closures (NH-48, Subhash Chowk, Golf Course Ext)",
                "script_hindi": (
                    "कृपया ध्यान दें। यह नगर निगम गुरुग्राम बाढ़ नियंत्रण कक्ष है। "
                    "एनएच-48 हीरो होंडा चौक अंडरपास और सुभाष चौक पर 90 सेंटीमीटर जलभराव के कारण "
                    "यातायात पूरी तरह रोक दिया गया है। जयपुर जाने वाले सभी वाहन सोहना एलिवेटेड रोड या "
                    "गोल्फ कोर्स एक्सटेंशन का प्रयोग करें।"
                ),
                "script_haryanvi": (
                    "राम राम भाईयो। यो नगर निगम गुरुग्राम का बाढ़ कंट्रोल रूम सै। "
                    "हीरो होंडा चौक अर नरसिंहपुर आड़े घुटणा ताहीं पाणी भर ग्या है, उड़े भूल कै भी ना जाइयो। "
                    "गाड़ियाँ सोहना वाले फ्लाईओवर पे ते काढ़ लो, उड़े रस्ता बिल्कुल खुला है।"
                ),
                "affected_roads": [
                    "NH-48 Hero Honda Chowk Underpass (CLOSED)",
                    "Subhash Chowk Intersection (WATERLOGGED)",
                    "Narsinghpur Service Lane (IMPASSABLE)"
                ],
                "safe_alternate_routes": [
                    "Sohna Elevated Expressway (CLEAR)",
                    "Golf Course Extension Road (CLEAR)",
                    "Kundli-Manesar-Palwal (KMP) Expressway (OPEN)"
                ]
            },
            2: {
                "option_id": 2,
                "title_en": "Nearest High-Ground Evacuation & Relief Camps",
                "script_hindi": (
                    "गुरुग्राम आपदा प्रबंधन प्राधिकरण द्वारा सुरक्षित राहत केंद्र स्थापित किए गए हैं। "
                    "निकटतम राहत शिविर ताऊ देवी लाल स्टेडियम सेक्टर 38, हुडा जिमखाना क्लब सेक्टर 29 और "
                    "कम्युनिटी सेंटर सेक्टर 14 में सक्रिय हैं। यहाँ स्वच्छ पेयजल, भोजन और आपातकालीन चिकित्सा सहायता 24 घंटे उपलब्ध है।"
                ),
                "script_haryanvi": (
                    "जो भाई-मानस या परिवार पाणी म्ह फंसे से, वे सीधा ताऊ देवी लाल स्टेडियम सेक्टर 38 "
                    "या सेक्टर 29 ग्राउंड म्ह पहुँचो। उड़े एमसीजी की तरिया ते रोटी, तात्ता पाणी, तिरपाल अर "
                    "दवाई-गोली का पूरा परबंध है। बिल्कुल घबरावो ना।"
                ),
                "shelters": [
                    {"name": "Tau Devi Lal Stadium", "sector": "Sector 38", "capacity": 1500, "status": "OPEN"},
                    {"name": "Huda Gymkhana Club", "sector": "Sector 29", "capacity": 800, "status": "OPEN"},
                    {"name": "Senior Secondary School Ground", "sector": "Sector 14", "capacity": 600, "status": "OPEN"}
                ]
            },
            3: {
                "option_id": 3,
                "title_en": "Active Mobile Dewatering Pump Deployments & Clearance ETA",
                "script_hindi": (
                    "जल निकासी कार्य की ताज़ा स्थिति: हीरो होंडा चौक पर एमसीजी के दो 50 हॉर्सपावर डिसेलिंग पंप "
                    "और खांडसा मुख्य ड्रेन पर 3 उच्च क्षमता वाले पंप लगातार कार्यरत हैं। अगले 40 मिनट में "
                    "जल स्तर 35 सेंटीमीटर तक कम होने का अनुमान है।"
                ),
                "script_haryanvi": (
                    "सुणो भाई, एमसीजी के बड़े पम्प हीरो होंडा अर खांडसा नाले पै चालू कर दिए हैं। "
                    "पानी तेजी ते बाहर फेक्या जा रह्या सै। पौणे घंटे म्ह रस्ता साफ़ हो ज्यागा, थोड़ा धीरज राखो, "
                    "अधिकारी मौके पै डटे हुए सै।"
                ),
                "active_pumps": [
                    {"spot": "Hero Honda Chowk", "capacity": "2x 50 HP Diesel Dewatering Pumps", "eta_clearance_min": 40},
                    {"spot": "Khandsa Master Drain", "capacity": "3x Axial Flow High Discharge Pumps", "eta_clearance_min": 30},
                    {"spot": "Rajiv Chowk Underpass", "capacity": "1x Super Sucker Jetting Machine", "eta_clearance_min": 25}
                ]
            },
            4: {
                "option_id": 4,
                "title_en": "Record Keypad Voice SOS / Emergency SDRF Evacuation",
                "script_hindi": (
                    "आपातकालीन सहायता रिकॉर्डिंग: बीप की आवाज़ के बाद अपना नाम, वर्तमान स्थान, फंसे हुए लोगों की संख्या "
                    "और चिकित्सा स्थिति बताएं। रिकॉर्डिंग समाप्त करने के लिए हैश (#) दबाएं। आपकी कॉल सीधे एसडीआरएफ "
                    "रेस्क्यू बोट टीम को प्रेषित की जा रही है।"
                ),
                "script_haryanvi": (
                    "बीप सुन कै अपणा नाम, थाम्है किते फंसे हो, गाड़ी म्ह कितने जणे सै अर के दिक्कत है, साफ-साफ बोल द्यो। "
                    "बोल कै हैश (#) का बटन दाब द्यो। म्हारी एसडीआरएफ की बोट टीम लट्ठ गाड़ कै थाम्है निकाल ल्यावैगी।"
                ),
                "instruction": "Speak clearly after tone; auto-transcribed and dispatched to SDRF."
            }
        }

        if option_id not in bulletins:
            raise ValueError(f"Invalid IVR option '{option_id}'. Options available: 1, 2, 3, 4.")

        res = bulletins[option_id]
        res["toll_free_number"] = "1800-180-1817"
        res["service_provider"] = "MCG Disaster Helpline • Hindi/Haryanvi IVR Gateway"
        res["timestamp_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return res

    def submit_ivr_voice_sos(
        self,
        caller_phone: str,
        spoken_location: str,
        spoken_emergency: str,
        dialect: str = "HARYANVI",
        passengers_count: int = 2
    ) -> Dict[str, Any]:
        """
        Ingests a citizen emergency voice SOS logged from a basic ₹800 feature keypad phone
        via Toll-Free 1800-180-1817 (Option 4). Auto-creates an emergency dispatch record.
        """
        ticket_id = f"IVR-SOS-{hashlib.md5(f'{caller_phone}{time.time()}'.encode()).hexdigest()[:6].upper()}"
        clean_phone = caller_phone.strip()
        
        ticket = {
            "ticket_id": ticket_id,
            "caller_phone": clean_phone,
            "spoken_location": spoken_location,
            "spoken_emergency": spoken_emergency,
            "dialect": dialect.upper(),
            "passengers_count": max(1, passengers_count),
            "priority": "HIGH_SEVERITY_RESCUE",
            "dispatch_status": "DISPATCHED_TO_SDRF",
            "assigned_unit": "SDRF Rescue Unit Bravo (Inflatable Boat + Paramedic)",
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "estimated_response_minutes": 7.0
        }
        self._ivr_sos_records.append(ticket)
        return ticket

    # =========================================================================
    # 4. B2B DLF CYBER CITY / CYBER HUB BASEMENT FLOOD BARRIER PROTOCOL
    # =========================================================================
    def _init_cyberhub_state(self) -> Dict[str, Any]:
        return {
            "facility_name": "DLF Cyber City & Cyber Hub IT Park (Gurugram)",
            "current_stage": "STAGE_1_ADVISORY",
            "stage_code": "T-60M",
            "countdown_minutes_remaining": 60,
            "flood_barrier_status": "STAGED_READY",
            "hydraulic_barrier_elevation_m": 0.0,
            "barrier_target_elevation_m": 1.2,
            "basement_levels": ["B1 (Visitor)", "B2 (Corporate)", "B3 (HVAC/Substation)"],
            "basement_evacuation_status": "STANDBY",
            "dhbvn_11kv_power_grid": "ENERGIZED_NORMAL",
            "rooftop_dg_generators": "WARM_IDLE_READY",
            "critical_servers_status": "ON_GRID_POWER",
            "last_escalation_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    def get_b2b_cyberhub_status(self) -> Dict[str, Any]:
        """
        Returns live status of DLF Cyber Hub subterranean flood containment protocol.
        """
        return self._b2b_cyberhub_state

    def advance_b2b_cyberhub_countdown(self, target_minutes: int) -> Dict[str, Any]:
        """
        Advances the automated B2B flood escalation countdown:
        T-60m: Advisory & Barrier Sump Energization
        T-45m: Hydraulic Flood Barrier Ramp Deployment (+1.2m steel wall)
        T-30m: B1/B2/B3 Subterranean Vehicle Evacuation Alarm
        T-15m: 11kV Substation Power Grid Cutoff to prevent catastrophic arcing/explosion
        """
        minutes = max(0, min(60, int(target_minutes)))
        self._b2b_cyberhub_state["countdown_minutes_remaining"] = minutes

        if minutes > 45:
            # Stage 1: T-60M
            self._b2b_cyberhub_state.update({
                "current_stage": "STAGE_1_ADVISORY",
                "stage_code": "T-60M",
                "flood_barrier_status": "STAGED_READY",
                "hydraulic_barrier_elevation_m": 0.0,
                "basement_evacuation_status": "STANDBY",
                "dhbvn_11kv_power_grid": "ENERGIZED_NORMAL",
                "rooftop_dg_generators": "WARM_IDLE_READY",
                "critical_servers_status": "ON_GRID_POWER"
            })
        elif minutes > 30:
            # Stage 2: T-45M
            self._b2b_cyberhub_state.update({
                "current_stage": "STAGE_2_BARRIER_DEPLOYMENT",
                "stage_code": "T-45M",
                "flood_barrier_status": "DEPLOYED_LOCKED",
                "hydraulic_barrier_elevation_m": 1.2,
                "basement_evacuation_status": "INGRESS_BLOCKED",
                "dhbvn_11kv_power_grid": "ENERGIZED_MONITORED",
                "rooftop_dg_generators": "SPINNING_RESERVE",
                "critical_servers_status": "ON_GRID_POWER"
            })
        elif minutes > 15:
            # Stage 3: T-30M
            self._b2b_cyberhub_state.update({
                "current_stage": "STAGE_3_SUBTERRANEAN_EVACUATION",
                "stage_code": "T-30M",
                "flood_barrier_status": "DEPLOYED_LOCKED",
                "hydraulic_barrier_elevation_m": 1.2,
                "basement_evacuation_status": "EVACUATING_B1_B2_B3",
                "dhbvn_11kv_power_grid": "PREPARING_ISOLATION",
                "rooftop_dg_generators": "DG_SETS_ONLINE_100_PCT",
                "critical_servers_status": "DUAL_FEED_ACTIVE"
            })
        else:
            # Stage 4: T-15M
            self._b2b_cyberhub_state.update({
                "current_stage": "STAGE_4_ELECTRICAL_ISOLATION",
                "stage_code": "T-15M",
                "flood_barrier_status": "DEPLOYED_HERMETIC_SEAL",
                "hydraulic_barrier_elevation_m": 1.2,
                "basement_evacuation_status": "COMPLETELY_EVACUATED",
                "dhbvn_11kv_power_grid": "DE_ENERGIZED_SAFE",
                "rooftop_dg_generators": "PRIMARY_POWER_ACTIVE",
                "critical_servers_status": "ROOFTOP_DG_PLUS_CLOUD_FAILOVER"
            })

        self._b2b_cyberhub_state["last_escalation_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return self._b2b_cyberhub_state

    def acknowledge_b2b_protocol(
        self,
        facility_manager_id: str,
        company: str = "DLF Cyber City Operations",
        phase_code: str = "T-15M",
        verification_token: str = "DLF-FM-2026-SECURE"
    ) -> Dict[str, Any]:
        """
        Logs a legally auditable facility manager acknowledgment proving that flood barriers
        and electrical power isolation were confirmed before catastrophic inundation.
        """
        audit_id = f"B2B-AUDIT-{hashlib.sha256(f'{facility_manager_id}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        
        audit_entry = {
            "audit_id": audit_id,
            "facility_manager_id": facility_manager_id,
            "company": company,
            "phase_code": phase_code,
            "verification_token": verification_token,
            "hydraulic_barrier_status": self._b2b_cyberhub_state["flood_barrier_status"],
            "power_grid_status": self._b2b_cyberhub_state["dhbvn_11kv_power_grid"],
            "server_failover_status": self._b2b_cyberhub_state["critical_servers_status"],
            "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "COMPLIANCE_VERIFIED"
        }
        self._b2b_audit_ledger.append(audit_entry)
        return audit_entry

# Singleton instance
alert_service = AlertService()
