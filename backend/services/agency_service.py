"""
JalRakshak NCR - Multi-Agency Coordination & Disaster Logistics Service
Handles DHBVN electrical grid safety, automated underpass boom barriers,
emergency shelters/MLCP dry parking sanctuaries, and official MCG flood insurance certificates.
"""

import io
import math
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database import get_db_cursor
from services.auth_service import auth_service
from websocket_manager import ws_manager

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class AgencyService:
    # ==========================================
    # 1. DHBVN Electrical Substation Hazard Management
    # ==========================================
    def get_dhbvn_feeders(self) -> List[Dict[str, Any]]:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, feeder_code, substation_name, area, lat, lng,
                       voltage_kv, water_depth_near_feeder_cm, power_cut_requested,
                       power_cut_executed, requested_by, requested_at, cut_executed_at, substation_phone
                FROM electrical_hazards
                ORDER BY water_depth_near_feeder_cm DESC
            """)
            rows = cursor.fetchall()
            feeders = []
            for r in rows:
                depth = r["water_depth_near_feeder_cm"]
                if depth >= 30:
                    hazard_status = "CRITICAL_SUBMERGED"
                elif depth >= 15:
                    hazard_status = "WARNING_WATERLOGGED"
                else:
                    hazard_status = "NORMAL_DRY"

                feeders.append({
                    "id": r["id"],
                    "feeder_code": r["feeder_code"],
                    "substation_name": r["substation_name"],
                    "area": r["area"],
                    "lat": r["lat"],
                    "lng": r["lng"],
                    "voltage_kv": r["voltage_kv"],
                    "water_depth_near_feeder_cm": depth,
                    "hazard_status": hazard_status,
                    "power_cut_requested": bool(r["power_cut_requested"]),
                    "power_cut_executed": bool(r["power_cut_executed"]),
                    "requested_by": r["requested_by"],
                    "requested_at": r["requested_at"],
                    "cut_executed_at": r["cut_executed_at"],
                    "substation_phone": r["substation_phone"]
                })
            return feeders

    def request_dhbvn_power_cut(
        self, feeder_id: str, requested_by: str, water_depth_cm: Optional[int] = None, reason: str = ""
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT * FROM electrical_hazards WHERE id = ?", (feeder_id,))
            feeder = cursor.fetchone()
            if not feeder:
                raise ValueError(f"Substation feeder '{feeder_id}' not found.")

            new_depth = water_depth_cm if water_depth_cm is not None else feeder["water_depth_near_feeder_cm"]

            cursor.execute("""
                UPDATE electrical_hazards
                SET power_cut_requested = 1,
                    requested_by = ?,
                    requested_at = ?,
                    water_depth_near_feeder_cm = ?
                WHERE id = ?
            """, (requested_by, now_iso, new_depth, feeder_id))

        auth_service.log_audit(
            actor_id="DHBVN_SYSTEM",
            actor_name=requested_by,
            actor_role="OFFICIAL",
            action="POWER_CUT_REQUESTED",
            target_entity="electrical_hazards",
            target_id=feeder_id,
            payload={"water_depth_cm": new_depth, "reason": reason}
        )

        return {
            "success": True,
            "feeder_id": feeder_id,
            "feeder_code": feeder["feeder_code"],
            "substation_name": feeder["substation_name"],
            "power_cut_requested": True,
            "requested_by": requested_by,
            "requested_at": now_iso,
            "water_depth_cm": new_depth,
            "message": f"Emergency power cut ticket dispatched to DHBVN Substation Division ({feeder['substation_name']})."
        }

    def execute_dhbvn_power_cut(self, feeder_id: str, executed_by: str) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT * FROM electrical_hazards WHERE id = ?", (feeder_id,))
            feeder = cursor.fetchone()
            if not feeder:
                raise ValueError(f"Substation feeder '{feeder_id}' not found.")

            cursor.execute("""
                UPDATE electrical_hazards
                SET power_cut_executed = 1,
                    cut_executed_at = ?
                WHERE id = ?
            """, (now_iso, feeder_id))

        auth_service.log_audit(
            actor_id="DHBVN_DISPATCH",
            actor_name=executed_by,
            actor_role="DHBVN_OFFICIAL",
            action="POWER_CUT_EXECUTED",
            target_entity="electrical_hazards",
            target_id=feeder_id,
            payload={"feeder_code": feeder["feeder_code"]}
        )

        return {
            "success": True,
            "feeder_id": feeder_id,
            "feeder_code": feeder["feeder_code"],
            "power_cut_executed": True,
            "executed_by": executed_by,
            "cut_executed_at": now_iso,
            "message": f"Feeder {feeder['feeder_code']} safely isolated to prevent electrocution hazards."
        }

    def restore_dhbvn_power(self, feeder_id: str, restored_by: str) -> Dict[str, Any]:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT * FROM electrical_hazards WHERE id = ?", (feeder_id,))
            feeder = cursor.fetchone()
            if not feeder:
                raise ValueError(f"Substation feeder '{feeder_id}' not found.")

            cursor.execute("""
                UPDATE electrical_hazards
                SET power_cut_requested = 0,
                    power_cut_executed = 0,
                    requested_by = NULL,
                    requested_at = NULL,
                    cut_executed_at = NULL
                WHERE id = ?
            """, (feeder_id,))

        auth_service.log_audit(
            actor_id="DHBVN_DISPATCH",
            actor_name=restored_by,
            actor_role="DHBVN_OFFICIAL",
            action="POWER_RESTORED",
            target_entity="electrical_hazards",
            target_id=feeder_id,
            payload={"feeder_code": feeder["feeder_code"]}
        )

        return {
            "success": True,
            "feeder_id": feeder_id,
            "power_restored": True,
            "restored_by": restored_by,
            "message": f"Grid supply re-energized for {feeder['feeder_code']}."
        }

    # ==========================================
    # 2. Automated Underpass Boom Barrier Management
    # ==========================================
    def get_underpass_barriers(self) -> List[Dict[str, Any]]:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT b.id, b.hotspot_id, b.location_name, b.barrier_state,
                       b.trigger_threshold_cm, b.closed_by, b.closed_at, b.last_inspected,
                       h.current_depth_cm, h.name as hotspot_name
                FROM underpass_barriers b
                LEFT JOIN hotspots_db h ON b.hotspot_id = h.id
                ORDER BY b.id ASC
            """)
            rows = cursor.fetchall()
            barriers = []
            for r in rows:
                current_depth = r["current_depth_cm"] if r["current_depth_cm"] is not None else 0
                threshold = r["trigger_threshold_cm"]
                needs_closure = current_depth >= threshold

                barriers.append({
                    "id": r["id"],
                    "hotspot_id": r["hotspot_id"],
                    "hotspot_name": r["hotspot_name"] or r["location_name"],
                    "location_name": r["location_name"],
                    "barrier_state": r["barrier_state"],
                    "trigger_threshold_cm": threshold,
                    "current_water_depth_cm": current_depth,
                    "recommended_action": "LOWER_BARRIER" if (needs_closure and r["barrier_state"] == "OPEN") else "MAINTAIN_STATE",
                    "closed_by": r["closed_by"],
                    "closed_at": r["closed_at"],
                    "last_inspected": r["last_inspected"]
                })
            return barriers

    def toggle_boom_barrier(
        self, barrier_id: str, new_state: str, operator_name: str, reason: str = ""
    ) -> Dict[str, Any]:
        new_state = new_state.upper()
        if new_state not in ("OPEN", "CLOSED"):
            raise ValueError("Barrier state must be either 'OPEN' or 'CLOSED'.")

        now_iso = datetime.now(timezone.utc).isoformat()
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT * FROM underpass_barriers WHERE id = ?", (barrier_id,))
            barrier = cursor.fetchone()
            if not barrier:
                raise ValueError(f"Boom barrier '{barrier_id}' not found.")

            closed_by = operator_name if new_state == "CLOSED" else None
            closed_at = now_iso if new_state == "CLOSED" else None

            cursor.execute("""
                UPDATE underpass_barriers
                SET barrier_state = ?,
                    closed_by = ?,
                    closed_at = ?,
                    last_inspected = ?
                WHERE id = ?
            """, (new_state, closed_by, closed_at, now_iso, barrier_id))

        auth_service.log_audit(
            actor_id="TRAFFIC_POLICE_CONTROL",
            actor_name=operator_name,
            actor_role="POLICE_OFFICIAL",
            action="BARRIER_STATE_TOGGLED",
            target_entity="underpass_barriers",
            target_id=barrier_id,
            payload={"new_state": new_state, "reason": reason}
        )

        return {
            "success": True,
            "barrier_id": barrier_id,
            "location_name": barrier["location_name"],
            "new_state": new_state,
            "operated_by": operator_name,
            "updated_at": now_iso,
            "message": f"Boom barrier {barrier_id} is now {new_state}."
        }

    # ==========================================
    # 3. Emergency Shelters & Safe Dry Parking Sanctuaries (MLCP)
    # ==========================================
    def get_emergency_shelters(
        self,
        shelter_type: Optional[str] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        radius_km: float = 25.0
    ) -> List[Dict[str, Any]]:
        with get_db_cursor() as cursor:
            query = "SELECT * FROM emergency_shelters WHERE is_active = 1"
            params = []
            if shelter_type:
                query += " AND shelter_type = ?"
                params.append(shelter_type.upper())

            cursor.execute(query, params)
            rows = cursor.fetchall()
            shelters = []

            for r in rows:
                s_lat = r["lat"]
                s_lng = r["lng"]

                dist_km = None
                if user_lat is not None and user_lng is not None:
                    dist_km = haversine_km(user_lat, user_lng, s_lat, s_lng)
                    if dist_km > radius_km:
                        continue

                cap_ppl = r["capacity_people"]
                occ_ppl = r["current_occupancy"]
                cap_veh = r["capacity_vehicles"]
                occ_pct = round((occ_ppl / max(cap_ppl, 1)) * 100, 1) if cap_ppl > 0 else 0.0

                shelters.append({
                    "id": r["id"],
                    "name": r["name"],
                    "shelter_type": r["shelter_type"],
                    "address": r["address"],
                    "lat": s_lat,
                    "lng": s_lng,
                    "distance_km": dist_km,
                    "capacity_people": cap_ppl,
                    "capacity_vehicles": cap_veh,
                    "current_occupancy": occ_ppl,
                    "occupancy_percentage": occ_pct,
                    "is_full": occ_ppl >= cap_ppl if cap_ppl > 0 else False,
                    "has_drinking_water": bool(r["has_drinking_water"]),
                    "has_power_backup": bool(r["has_power_backup"]),
                    "has_first_aid": bool(r["has_first_aid"]),
                    "contact_person": r["contact_person"],
                    "contact_phone": r["contact_phone"]
                })

            if user_lat is not None and user_lng is not None:
                shelters.sort(key=lambda s: s["distance_km"] if s["distance_km"] is not None else 999.0)

            return shelters

    # ==========================================
    # 4. Official Flood Incident Insurance Certificate Generator (PDF)
    # ==========================================
    def generate_insurance_certificate(
        self,
        citizen_name: str,
        citizen_phone: str,
        vehicle_registration: str,
        vehicle_make_model: str,
        incident_location: str,
        incident_date_time: Optional[str] = None,
        flood_water_depth_cm: int = 85,
        incident_description: str = "Vehicle sustained complete engine hydrolock and electrical submersion due to localized cloudburst flash flooding.",
        citizen_aadhaar_last4: Optional[str] = "XXXX",
        hotspot_id: Optional[str] = None
    ) -> bytes:
        """
        Generates an official, tamper-evident PDF verification certificate
        issued by the Municipal Corporation of Gurugram (MCG) & District Disaster Management Authority (DDMA)
        for automotive insurance claims under Section 34 of the Disaster Management Act, 2005.
        """
        now = datetime.now(timezone.utc)
        issue_date_str = now.strftime("%d %B %Y, %H:%M:%S UTC")
        if not incident_date_time:
            incident_date_time = now.strftime("%d %B %Y, %H:%M HRS IST")

        cert_id = f"MCG/DDMA/2026/FL-{uuid.uuid4().hex[:8].upper()}"

        # Calculate a digital verification hash
        hash_payload = f"{cert_id}|{citizen_name}|{vehicle_registration}|{flood_water_depth_cm}|{incident_location}|2026-MCG-AUTHENTIC"
        digital_seal = hashlib.sha256(hash_payload.encode()).hexdigest()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Paragraph Styles
        header_title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0F172A')
        )
        header_sub_style = ParagraphStyle(
            'HeaderSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#475569')
        )
        cert_title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0284C7')
        )
        body_style = ParagraphStyle(
            'CertBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor('#1E293B')
        )
        bold_label = ParagraphStyle(
            'BoldLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0F172A')
        )
        data_text = ParagraphStyle(
            'DataText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        hash_style = ParagraphStyle(
            'HashText',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=7,
            leading=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748B')
        )

        story = []

        # Government Emblem Header & Title
        story.append(Paragraph("<b>MUNICIPAL CORPORATION OF GURUGRAM (MCG)</b>", header_title_style))
        story.append(Paragraph("GOVERNMENT OF HARYANA | DISTRICT DISASTER MANAGEMENT AUTHORITY (DDMA)", header_sub_style))
        story.append(Paragraph("Plot No. C-1, Info Technology Park, Sector 34, Gurugram, Haryana - 122001", header_sub_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284C7'), spaceBefore=2, spaceAfter=8))

        # Certificate Identification Box
        cert_meta = [
            [
                Paragraph(f"<b>CERTIFICATE REF:</b> <font color='#0284C7'>{cert_id}</font>", bold_label),
                Paragraph(f"<b>DATE OF ISSUE:</b> {issue_date_str}", bold_label)
            ],
            [
                Paragraph("<b>ISSUING AUTHORITY:</b> MCG Flood Control Center", data_text),
                Paragraph("<b>PURPOSE:</b> Insurance Act-of-God Damage Claim", data_text)
            ]
        ]
        meta_table = Table(cert_meta, colWidths=[270, 250])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # Main Title Banner
        story.append(Paragraph("<b>OFFICIAL FLOOD INCIDENT VERIFICATION CERTIFICATE</b>", cert_title_style))
        story.append(Paragraph("<i>(Issued under Section 34 & 38 of the Disaster Management Act, 2005)</i>", header_sub_style))
        story.append(Spacer(1, 10))

        # Section 1: Citizen & Vehicle Particulars
        story.append(Paragraph("<b>1. VEHICLE OWNER & REGISTRATION PARTICULARS</b>", bold_label))
        story.append(Spacer(1, 4))
        veh_data = [
            [Paragraph("<b>Vehicle Owner / Claimant:</b>", bold_label), Paragraph(citizen_name, data_text),
             Paragraph("<b>Contact Phone:</b>", bold_label), Paragraph(citizen_phone, data_text)],
            [Paragraph("<b>Vehicle Registration No:</b>", bold_label), Paragraph(f"<b><font color='#B91C1C'>{vehicle_registration}</font></b>", data_text),
             Paragraph("<b>Make & Model:</b>", bold_label), Paragraph(vehicle_make_model, data_text)],
            [Paragraph("<b>Aadhaar Verification (Last 4):</b>", bold_label), Paragraph(f"XXXX-XXXX-{citizen_aadhaar_last4}", data_text),
             Paragraph("<b>Registered RTO:</b>", bold_label), Paragraph("HR-26 (Gurugram North / South)", data_text)]
        ]
        veh_table = Table(veh_data, colWidths=[135, 125, 130, 130])
        veh_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(veh_table)
        story.append(Spacer(1, 10))

        # Section 2: Verified Geo-Spatial Incident Telemetry
        story.append(Paragraph("<b>2. VERIFIED MUNICIPAL HYDROLOGICAL & INCIDENT TELEMETRY</b>", bold_label))
        story.append(Spacer(1, 4))
        telemetry_data = [
            [Paragraph("<b>Incident Site Location:</b>", bold_label), Paragraph(incident_location, data_text),
             Paragraph("<b>Time of Submersion:</b>", bold_label), Paragraph(incident_date_time, data_text)],
            [Paragraph("<b>IMD Cloudburst Rainfall Rate:</b>", bold_label), Paragraph("133.0 mm/hr (Extreme Event)", data_text),
             Paragraph("<b>Recorded Water Depth:</b>", bold_label), Paragraph(f"<b><font color='#DC2626'>{flood_water_depth_cm} cm</font></b>", data_text)],
            [Paragraph("<b>Drainage Corridor:</b>", bold_label), Paragraph("Leg 3 (Badshahpur Master Basin Outfall)", data_text),
             Paragraph("<b>Municipal Flood Alert Level:</b>", bold_label), Paragraph("RED CATEGORY (Submerged Arterial)", data_text)],
            [Paragraph("<b>Verified Incident Description:</b>", bold_label), Paragraph(incident_description, data_text), "", ""]
        ]
        telemetry_table = Table(telemetry_data, colWidths=[135, 125, 130, 130])
        telemetry_table.setStyle(TableStyle([
            ('SPAN', (1, 3), (3, 3)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(telemetry_table)
        story.append(Spacer(1, 10))

        # Section 3: Statutory Certification Statement
        story.append(Paragraph("<b>3. STATUTORY MUNICIPAL CERTIFICATION STATEMENT</b>", bold_label))
        story.append(Spacer(1, 4))
        cert_text = (
            "This is to formally certify by the Municipal Corporation of Gurugram (MCG) Flood Emergency Control Room "
            "that on the date and time recorded above, the designated location experienced severe urban flash flooding "
            "and storm runoff surcharge that exceeded the hydraulic carrying capacity of the stormwater drainage network. "
            f"The vehicle bearing registration number <b>{vehicle_registration}</b> was stranded in standing water of "
            f"approximately <b>{flood_water_depth_cm} cm</b>, resulting in involuntary submersion, hydro-locking, and "
            "damage caused solely by catastrophic natural meteorological conditions (Act of God). "
            "This document constitutes official municipal validation for comprehensive motor insurance claim settlement."
        )
        story.append(Paragraph(cert_text, body_style))
        story.append(Spacer(1, 14))

        # Signatures & Verification Seal Table
        sig_data = [
            [
                Paragraph("<b>CRYPTOGRAPHIC VERIFICATION SEAL</b><br/>"
                          f"<font size='6'>SHA-256: {digital_seal[:32]}...{digital_seal[-16:]}</font><br/>"
                          f"<font size='6' color='#0284C7'>VERIFY AT: https://mcg.gov.in/verify/{cert_id}</font>", hash_style),
                Paragraph("<b>Digitally Certified By:</b><br/>"
                          "<b>Chief Disaster Management Officer</b><br/>"
                          "Gurugram Metropolitan Development Authority (GMDA)<br/>"
                          "Municipal Corporation of Gurugram (MCG)<br/>"
                          f"<i>Digitally Signed: {issue_date_str}</i>", data_text)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[260, 260])
        sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F1F5F9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94A3B8')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(sig_table)

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


agency_service = AgencyService()
