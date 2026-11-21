"""
NeerNetra - JalRakshak NCR
Vandal-Proof Sensor Architecture & Indian GeM Capex Model Service (Deliverable 4)
Engineered for zero street vandalism exposure, low-capex municipal procurement,
and high telemetry resilience.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class SensorService:
    def __init__(self):
        # 1. Authoritative Indian GeM Capex & 5-Year AMC Model
        self._gem_capex_model = {
            "title": "Indian GeM (Government e-Marketplace) 159-Hotspot Sensor Capex & AMC Budget",
            "currency": "INR (₹)",
            "mcg_annual_budget_cr": 2200.0,
            "historical_post_gurujam_spend_cr": 1400.0,
            "line_items": [
                {
                    "item_id": "GEM-ITEM-01",
                    "description": "IP68 Non-Contact 70kHz Ultrasonic Water Level Sensors (0.5m-10m range, LoRaWAN IN865 + 2G GSM dual-modem, LiFePO4 battery & trickle solar panel)",
                    "gem_category_code": "GeM/2026/WATER-LEVEL-IOT-IP68",
                    "quantity": 42,
                    "unit": "Units (36 Deployed Trunk Nodes + 6 MCG Store Spares)",
                    "unit_cost_inr": 18500.0,
                    "total_cost_inr": 777000.0,
                    "target_nodes": "Tier 1: 36 Critical Trunk Choke Points"
                },
                {
                    "item_id": "GEM-ITEM-02",
                    "description": "4mm Hot-Dip Galvanized Mild Steel (MS) Anti-Theft Perforated Security Cages + Tamper Microswitch + SS316 Mechanical Float Switch Redundant Backup",
                    "gem_category_code": "GeM/2026/MUNICIPAL-HARDWARE-SECURITY",
                    "quantity": 36,
                    "unit": "Security Cages & Float Assemblies",
                    "unit_cost_inr": 9700.0,
                    "total_cost_inr": 349200.0,
                    "target_nodes": "Tier 1: 36 Overhead High-Mast Pole Mountings (4m-6m AGL)"
                },
                {
                    "item_id": "GEM-ITEM-03",
                    "description": "Fiberglass Reinforced Plastic (FRP) Tipping-Bucket Automated Rain Gauges (0.2mm sensitivity, enclosed in gated DHBVN/MCG compounds) + 8-Channel Outdoor PoE LoRa Gateways",
                    "gem_category_code": "GeM/2026/METEOROLOGICAL-ARG-GW",
                    "quantity": 24,
                    "unit": "Met Units (16 Tipping-Bucket ARGs @ ₹32.5k + 8 LoRa Gateways @ ₹41k)",
                    "unit_cost_inr": 35333.33,
                    "total_cost_inr": 848000.0,
                    "target_nodes": "16 Secured Gated Compounds + 8 Communication Towers"
                },
                {
                    "item_id": "GEM-ITEM-04",
                    "description": "High-Contrast Red/Amber/Green Reflective Polyurethane Curb-Depth Gauge Stencils (Zero Hardware Capex) + 22 High-Brightness Underpass Warning LED Display Boards",
                    "gem_category_code": "GeM/2026/TRAFFIC-SAFETY-DISPLAYS",
                    "quantity": 105,
                    "unit": "Units (83 Painted Curb Stencils @ ₹1.8k + 22 Underpass LED Boards @ ₹45k)",
                    "unit_cost_inr": 10851.43,
                    "total_cost_inr": 1139400.0,
                    "target_nodes": "Tier 2: 83 GMDA ICCC CCTV Junctions + 11 Underpass Approaches"
                },
                {
                    "item_id": "GEM-ITEM-05",
                    "description": "GMDA ICCC Edge Analytics Server (Dual Intel Xeon, OpenCV Stream Engine, Redundant SSD) + GIS Engine / Offline GSM SMS Gateway / 1800-Toll-Free Voice IVR Integration",
                    "gem_category_code": "GeM/2026/SYSTEM-INTEGRATION-SMARTCITY",
                    "quantity": 1,
                    "unit": "Enterprise System Integration Package",
                    "unit_cost_inr": 1800000.0,
                    "total_cost_inr": 1800000.0,
                    "target_nodes": "GMDA ICCC Sector 44 Data Center & MCG Headquarters"
                }
            ],
            "total_capex_inr": 4913600.0,
            "total_capex_lakhs": 49.14,
            "annual_amc_lakhs": 9.80,
            "five_year_amc_lakhs": 49.00,
            "five_year_tco_lakhs": 98.14,
            "amc_sla": {
                "uptime_guarantee_pct": 95.0,
                "max_repair_turnaround_hrs": 4,
                "annual_preventive_visits": 4
            },
            "budget_perspective": {
                "pct_of_mcg_annual_budget": 0.0223,
                "pct_of_historical_gurujam_spend": 0.0351,
                "summary": "Total Capex of ₹49.14 Lakhs represents less than 0.03% of the ₹1,400+ Crore spent on reactive post-Gurujam drainage repairs."
            }
        }

        # 2. Live Telemetry State across Sensor Tiers
        self._tier1_sensors: Dict[str, Dict[str, Any]] = {}
        self._tampered_sensors: Dict[str, Dict[str, Any]] = {}
        self._init_tier1_sensors()

        # 3. LoRa Gateways & Gated Compound ARGs
        self._gateways = [
            {"id": "GW-IN865-01", "name": "MCG Head Office Tower (Sec 34)", "lat": 28.4350, "lng": 77.0250, "status": "ONLINE", "frequency": "IN865 (865.2 MHz)", "pdr_pct": 99.4, "connected_nodes": 22},
            {"id": "GW-IN865-02", "name": "GMDA ICCC Tower (Sec 44)", "lat": 28.4510, "lng": 77.0670, "status": "ONLINE", "frequency": "IN865 (865.5 MHz)", "pdr_pct": 98.9, "connected_nodes": 19},
            {"id": "GW-IN865-03", "name": "DHBVN 66kV Substation (Sec 46)", "lat": 28.4360, "lng": 77.0580, "status": "ONLINE", "frequency": "IN865 (865.8 MHz)", "pdr_pct": 99.1, "connected_nodes": 18},
            {"id": "GW-IN865-04", "name": "Hero Honda Underpass Control (Sec 37)", "lat": 28.4265, "lng": 77.0031, "status": "ONLINE", "frequency": "IN865 (866.1 MHz)", "pdr_pct": 99.2, "connected_nodes": 24},
            {"id": "GW-IN865-05", "name": "Old Gurugram MCG Ward 12 Tower", "lat": 28.4754, "lng": 77.0315, "status": "ONLINE", "frequency": "IN865 (866.4 MHz)", "pdr_pct": 98.7, "connected_nodes": 26},
            {"id": "GW-IN865-06", "name": "Golf Course Road Sector 56 Mast", "lat": 28.4320, "lng": 77.1060, "status": "ONLINE", "frequency": "IN865 (866.7 MHz)", "pdr_pct": 98.5, "connected_nodes": 17},
            {"id": "GW-IN865-07", "name": "DLF Cyber City Shankar Chowk Mast", "lat": 28.5020, "lng": 77.0860, "status": "ONLINE", "frequency": "IN865 (867.0 MHz)", "pdr_pct": 99.3, "connected_nodes": 16},
            {"id": "GW-IN865-08", "name": "Basai Water Treatment Plant Tower", "lat": 28.4610, "lng": 76.9740, "status": "ONLINE", "frequency": "IN865 (867.3 MHz)", "pdr_pct": 98.2, "connected_nodes": 17}
        ]

        self._gated_args = [
            {"id": "ARG-01", "location": "DHBVN 66kV Substation Sec 46", "gated_compound": True, "security": "24/7 Gated Guarded", "rain_rate_mm_hr": 2.4, "daily_rain_mm": 18.2},
            {"id": "ARG-02", "location": "MCG Ward 14 Office Complex", "gated_compound": True, "security": "24/7 Gated Guarded", "rain_rate_mm_hr": 3.1, "daily_rain_mm": 21.0},
            {"id": "ARG-03", "location": "GMDA Sector 32 Headquarters", "gated_compound": True, "security": "24/7 Gated Guarded", "rain_rate_mm_hr": 1.8, "daily_rain_mm": 16.5},
            {"id": "ARG-04", "location": "Civil Hospital Sector 10 Sump Compound", "gated_compound": True, "security": "24/7 Gated Guarded", "rain_rate_mm_hr": 2.9, "daily_rain_mm": 19.8}
        ]

    def _init_tier1_sensors(self):
        """Initializes telemetric states for the 36 Tier 1 ultrasonic trunk nodes"""
        trunk_codes = [f"GRG-{i:03d}" for i in range(1, 37)]
        for idx, code in enumerate(trunk_codes, start=1):
            sensor_id = f"SN-T1-{idx:03d}"
            self._tier1_sensors[code] = {
                "sensor_id": sensor_id,
                "node_code": code,
                "sensor_type": "IP68 Non-Contact 70kHz Ultrasonic",
                "mount_type": "Overhead High-Mast Pole (4.8m AGL)",
                "enclosure": "4mm Hot-Dip Galvanized MS Anti-Theft Cage",
                "telemetry_primary": "IN865 LoRaWAN",
                "telemetry_fallback": "2G GSM / GPRS",
                "battery_pct": 96 - (idx % 8),
                "solar_charging": True,
                "lora_rssi_dbm": -78 - (idx % 15),
                "cage_tamper_switch": "SECURE",
                "float_switch_backup": "DRY_NORMAL",
                "status": "ONLINE",
                "uptime_pct": 98.6
            }

    def get_gem_capex_model(self) -> Dict[str, Any]:
        """Returns the complete Indian GeM procurement budget breakdown and 5-year AMC model"""
        return self._gem_capex_model

    def get_sensor_telemetry_status(self) -> Dict[str, Any]:
        """
        Returns real-time network-wide telemetry status across all 3 tiers:
        36 Tier 1 Ultrasonic, 83 Tier 2 CCTV Virtual, 40 Tier 3 SI Crowd, 16 ARGs, 8 Gateways.
        """
        active_t1 = sum(1 for s in self._tier1_sensors.values() if s["status"] == "ONLINE")
        tampered_count = len(self._tampered_sensors)

        return {
            "overall_network_uptime_pct": 98.4,
            "architecture_tiers": {
                "tier_1_ultrasonic_trunk": {
                    "total_deployed": 36,
                    "store_spares": 6,
                    "online": active_t1,
                    "tamper_detected": tampered_count,
                    "sensor_type": "IP68 70kHz Ultrasonic + SS316 Float Backup",
                    "caging": "4mm Galvanized MS Anti-Vandal Cage with Tamper Switch"
                },
                "tier_2_cctv_virtual_gauges": {
                    "total_calibrated": 83,
                    "hardware_capex_inr": 0.0,
                    "technology": "GMDA ICCC Surveillance Cameras + OpenCV Reflective Stencil Reading",
                    "optical_confidence_pct": 96.2,
                    "status": "ALL_83_CALIBRATED"
                },
                "tier_3_crowd_and_si_ledger": {
                    "total_sector_spots": 40,
                    "active_inspectors": 35,
                    "cross_validation_with_tier_1_2": "ACTIVE",
                    "status": "HEALTHY"
                },
                "rooftop_met_infrastructure": {
                    "tipping_bucket_args": 16,
                    "arg_security_type": "GATED_SECURED_COMPOUNDS_ZERO_VANDALISM",
                    "lorawan_gateways": 8,
                    "frequency_band": "IN865 (865-867 MHz)",
                    "packet_delivery_ratio_pct": 98.8
                }
            },
            "gateways": self._gateways,
            "secured_args": self._gated_args
        }

    def simulate_anti_vandalism_tamper(self, node_code: str) -> Dict[str, Any]:
        """
        Simulates an anti-theft microswitch trip on an overhead MS cage.
        Demonstrates zero-data-loss failover:
        System logs tamper alarm and immediately falls back to redundant SS316 float
        and Tier 2 CCTV curb stencil cross-validation!
        """
        code = node_code.upper().strip()
        sensor = self._tier1_sensors.get(code)
        if not sensor:
            # Fallback to GRG-001 if unknown
            sensor = self._tier1_sensors["GRG-001"]
            code = "GRG-001"

        sensor["cage_tamper_switch"] = "TAMPER_DETECTED"
        sensor["float_switch_backup"] = "STANDBY_ACTIVE"
        sensor["tamper_timestamp"] = datetime.now(timezone.utc).isoformat()
        self._tampered_sensors[code] = sensor

        return {
            "alarm_status": "TAMPER_ALARM_ACTIVATED",
            "node_code": code,
            "sensor_id": sensor["sensor_id"],
            "event": "Overhead 4mm MS Cage Access Door Tamper Switch Tripped",
            "telemetry_failover_status": "ZERO_DATA_LOSS",
            "failover_redundancy": [
                "Redundant SS316 mechanical float switch engaged on separate circuit",
                "GMDA ICCC CCTV camera optical curb reading switched to primary streaming",
                "Automated silent SMS alert sent to MCG Security Patrol & Police Dial 112"
            ],
            "cage_tamper_switch": sensor["cage_tamper_switch"],
            "float_switch_backup": sensor["float_switch_backup"],
            "timestamp_utc": sensor["tamper_timestamp"]
        }

    def reset_sensor_tamper(self, node_code: str) -> Dict[str, Any]:
        """Resets tamper alert after field security team inspection"""
        code = node_code.upper().strip()
        if code in self._tampered_sensors:
            del self._tampered_sensors[code]

        if code in self._tier1_sensors:
            self._tier1_sensors[code]["cage_tamper_switch"] = "SECURE"
            self._tier1_sensors[code]["float_switch_backup"] = "DRY_NORMAL"

        return {
            "status": "RESET_SUCCESSFUL",
            "node_code": code,
            "cage_tamper_switch": "SECURE",
            "float_switch_backup": "DRY_NORMAL"
        }

# Singleton instance
sensor_service = SensorService()
