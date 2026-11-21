"""
NeerNetra - JalRakshak NCR
FastAPI Backend & ML Prediction Server (Deliverable 2)
Engineered for ultra-low latency (<5ms inference), explainable municipal outputs,
and high disaster resilience.
"""

import os
import sys
import json
import time
from typing import List, Optional, Set
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ml.predict_service import predict_hotspot_risk, predict_hotspots_batch, get_model
from topology_service import topology_service
from sop_service import sop_service
from sensor_service import sensor_service
from alert_service import alert_service
from database import init_db
from services.auth_service import auth_service
from routers.auth_router import router as auth_router
from routers.hotspot_router import router as hotspot_router
from routers.drain_router import router as drain_router
from routers.weather_router import router as weather_router
from routers.sos_router import router as sos_router
from routers.fleet_router import router as fleet_router
from routers.route_router import router as route_router
from routers.crowd_router import router as crowd_router
from routers.agency_router import router as agency_router
from websocket_manager import ws_manager
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI(
    title="JalRakshak NCR - Flood Prediction & AI Dispatch API",
    description="Engineered by Team NeerNetra for Municipal Corporation of Gurugram (MCG)",
    version="2.0.0"
)

# Initialize persistent database schema & seed default users on boot
init_db()
auth_service.seed_default_users()

# Mount Routers
app.include_router(auth_router)
app.include_router(hotspot_router)
app.include_router(drain_router)
app.include_router(weather_router)
app.include_router(sos_router)
app.include_router(fleet_router)
app.include_router(route_router)
app.include_router(crowd_router)
app.include_router(agency_router)

# ------------------ REAL-TIME WEBSOCKET GATEWAY ------------------
@app.websocket("/ws/live")
async def websocket_live_gateway(websocket: WebSocket, room: str = "general"):
    """
    Real-time bi-directional WebSocket connection for:
    - room='officials' (Command center siren alarms and live fleet movements)
    - room='citizen_{sos_id}' (Citizen rescue tracking and ETA)
    - room='drivers' (Fleet dispatch orders)
    """
    await ws_manager.connect(websocket, room)
    try:
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Enable CORS for local testing & GIS overlays
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ PYDANTIC SCHEMAS ------------------
class PredictionRequest(BaseModel):
    rainfall_mm_hr: float = Field(..., description="Current rain intensity in mm/hr", ge=0, le=250)
    cumulative_3h_rain_mm: float = Field(default=0.0, description="3-hour cumulative precipitation in mm", ge=0)
    elevation_m: float = Field(default=218.0, description="Spot ground elevation in meters (210 - 250m)")
    catchment_area_sqkm: float = Field(default=12.0, description="Upstream catchment runoff area in sq km")
    drain_silt_pct: float = Field(default=45.0, description="Drain siltation level (0-100%)", ge=0, le=100)
    pump_deployed: int = Field(default=0, description="1 if high-capacity pump active, else 0")
    critical_infra_proximity: int = Field(default=1, description="1 if highway/hospital/substation")

class SopCheckoffRequest(BaseModel):
    sop_id: str = Field(..., description="SOP ID or Phase Code, e.g. SOP-12H or T-12H")
    verified_by: str = Field(..., description="Name and title of verifying official (e.g. JE Sandeep)")
    notes: Optional[str] = Field(default=None, description="Field notes on staging status")

class AutoTriggerRequest(BaseModel):
    rain_mm_hr: float = Field(..., description="Live or simulated rainfall intensity in mm/hr", ge=0)

class FleetDispatchRequest(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle ID, e.g. TANKER-101 or QRV-401")
    target_location: str = Field(..., description="Destination road, choke point, or ward")
    requestor: str = Field(..., description="Calling entity: 'MCG Control Room', 'RWA President', etc.")
    is_vip_request: bool = Field(default=False, description="Flag for VIP/Councillor diversion requests")
    override_token: Optional[str] = Field(default=None, description="Commissioner Dual-Key Override Token if available")

class DualKeyOverrideRequest(BaseModel):
    reason: str = Field(..., description="Operational justification for temporary Ring-A trunk diversion")
    authorized_by: str = Field(default="Municipal Commissioner MCG", description="Authorizing executive")

class PublicCommitmentRequest(BaseModel):
    location_code: str = Field(..., description="Hotspot code e.g. GRG-002")
    location_name: str = Field(..., description="Hotspot name e.g. Hero Honda Chowk")
    predicted_depth_cm: float = Field(..., description="Unmitigated predicted water depth")
    actual_depth_cm: float = Field(..., description="Observed held water depth")
    mitigation_liters_lakh: float = Field(..., description="Volume pumped in Lakh Liters")
    staged_asset: str = Field(..., description="Pump tanker or crew staged")
    summary: str = Field(..., description="Proof summary for public commitment board")

class SensorTamperRequest(BaseModel):
    node_code: str = Field(default="GRG-001", description="Hotspot code to simulate cage tampering (e.g. GRG-001)")

class SmsGenerationRequest(BaseModel):
    lat: float = Field(..., description="WGS84 latitude coordinate")
    lng: float = Field(..., description="WGS84 longitude coordinate")
    hotspot_code: str = Field(default="GRG-002", description="Municipal node code (e.g. GRG-002)")
    depth_cm: float = Field(default=85.0, description="Measured or predicted flood water depth in cm")
    req_type: str = Field(default="EVAC", description="Emergency rescue category: EVAC, MEDICAL, BOAT_RESCUE, LIVE_WIRE")
    battery_pct: int = Field(default=85, description="Citizen phone battery percentage", ge=1, le=100)

class SmsParseRequest(BaseModel):
    raw_sms: str = Field(..., description="Raw inbound 160-byte SMS string")

class MeshRelayRequest(BaseModel):
    origin_lat: float = Field(default=28.4265, description="Origin latitude")
    origin_lng: float = Field(default=77.0031, description="Origin longitude")
    hotspot_code: str = Field(default="GRG-002", description="Location node code")
    incident_type: str = Field(default="STRANDED_VEHICLE", description="Nature of distress")
    distress_text: str = Field(default="Vehicle trapped in underpass, water at hood level", description="Distress notes")

class IvrSosRequest(BaseModel):
    caller_phone: str = Field(default="+91-98112-99887", description="Caller feature phone CLI")
    spoken_location: str = Field(default="Hero Honda Chowk underpass", description="Spoken voice location tag")
    spoken_emergency: str = Field(default="Water rising rapidly, elderly passenger onboard", description="Spoken voice emergency detail")
    dialect: str = Field(default="HARYANVI", description="Dialect preference: HINDI or HARYANVI")
    passengers_count: int = Field(default=2, description="Count of trapped individuals", ge=1)

class CyberHubCountdownRequest(BaseModel):
    target_minutes: int = Field(default=15, description="Minutes remaining until peak cloudburst surcharge (60 to 0)", ge=0, le=60)

class CyberHubAckRequest(BaseModel):
    facility_manager_id: str = Field(default="FM-RAVINDER-SINGH-DLF", description="Official DLF facility manager credential")
    company: str = Field(default="DLF Cyber City Operations", description="Facility entity name")
    phase_code: str = Field(default="T-15M", description="Escalation phase code being acknowledged")
    verification_token: str = Field(default="DLF-FM-2026-SECURE", description="Audit authorization token")

# Showcase Gurugram Hotspots default configurations
GURUGRAM_HOTSPOTS = [
    {
        "id": "hs_herohonda",
        "code": "GRG-102",
        "name": "Hero Honda Chowk Underpass",
        "leg": "LEG 3: BADSHAHPUR → KHANDSA CULVERT",
        "elevation_m": 215.2,
        "catchment_area_sqkm": 28.5,
        "default_silt_pct": 58.0,
        "lat": 28.4265,
        "lng": 77.0031
    },
    {
        "id": "hs_narsinghpur",
        "code": "GRG-108",
        "name": "Narsinghpur Stretch (NH-48)",
        "leg": "LEG 3: KHANDSA BACKWATER SINK",
        "elevation_m": 213.8,
        "catchment_area_sqkm": 34.0,
        "default_silt_pct": 62.0,
        "lat": 28.4024,
        "lng": 76.9796
    },
    {
        "id": "hs_rajiv",
        "code": "GRG-101",
        "name": "Rajiv Chowk Underpass",
        "leg": "LEG 3 LATERAL → NH-48 CROSSING",
        "elevation_m": 218.4,
        "catchment_area_sqkm": 16.2,
        "default_silt_pct": 48.0,
        "lat": 28.4449,
        "lng": 77.0345
    },
    {
        "id": "hs_medanta",
        "code": "GRG-103",
        "name": "Medanta Hospital Road",
        "leg": "LEG 3 COLLECTOR (SECTOR 38)",
        "elevation_m": 220.1,
        "catchment_area_sqkm": 8.5,
        "default_silt_pct": 44.0,
        "lat": 28.4394,
        "lng": 77.0416
    },
    {
        "id": "hs_subhash",
        "code": "GRG-106",
        "name": "Subhash Chowk (Sohna Rd)",
        "leg": "LEG 3 MIDSTREAM (BADSHAHPUR)",
        "elevation_m": 222.0,
        "catchment_area_sqkm": 11.0,
        "default_silt_pct": 41.0,
        "lat": 28.4283,
        "lng": 77.0398
    },
    {
        "id": "hs_iffco",
        "code": "GRG-104",
        "name": "IFFCO Chowk Metro",
        "leg": "LEG 2: CENTRAL SPINE CONDUIT",
        "elevation_m": 226.5,
        "catchment_area_sqkm": 9.2,
        "default_silt_pct": 15.0,
        "lat": 28.4773,
        "lng": 77.0689
    },
    {
        "id": "hs_sheetla",
        "code": "GRG-107",
        "name": "Sheetla Mata Road",
        "leg": "LEG 2 DOWNSTREAM → NAJAFGARH",
        "elevation_m": 219.0,
        "catchment_area_sqkm": 14.0,
        "default_silt_pct": 39.0,
        "lat": 28.4754,
        "lng": 77.0315
    },
    {
        "id": "hs_golfcourse",
        "code": "GRG-105",
        "name": "Golf Course Road (Sec 27)",
        "leg": "LEG 2 UPSTREAM (ARAVALLI RUNOFF)",
        "elevation_m": 241.5,
        "catchment_area_sqkm": 4.5,
        "default_silt_pct": 10.0,
        "lat": 28.4575,
        "lng": 77.0968
    }
]

# ------------------ API ENDPOINTS ------------------
@app.get("/api/health")
def health_check():
    """Health check verifying model status and memory footprint"""
    pkg = get_model()
    summary = topology_service.get_summary()
    return {
        "status": "healthy",
        "system": "JalRakshak NCR",
        "team": "NeerNetra",
        "model_loaded": True,
        "model_accuracy_pct": round(pkg.get("accuracy", 0.89) * 100, 2),
        "target_municipality": "Municipal Corporation of Gurugram (MCG)",
        "total_hotspots_indexed": summary.get("total_hotspots", 159),
        "pareto_coverage": summary.get("pareto_principle", {}).get("pareto_statement")
    }

# ------------------ TOPOLOGY ENDPOINTS (DELIVERABLE 1) ------------------
@app.get("/api/hotspots/159")
def get_all_hotspots(
    tier: Optional[int] = None,
    leg: Optional[str] = None,
    pareto_only: bool = False,
    ward: Optional[int] = None,
    search: Optional[str] = None
):
    """
    Returns queryable list from the authoritative 159-hotspot Gurugram drainage topology dataset.
    Supports sub-millisecond multi-attribute filtering.
    """
    hotspots = topology_service.get_all_hotspots(
        tier=tier,
        leg=leg,
        pareto_only=pareto_only,
        ward=ward,
        search=search
    )
    return {
        "count": len(hotspots),
        "total_indexed": 159,
        "filters_applied": {
            "tier": tier,
            "leg": leg,
            "pareto_only": pareto_only,
            "ward": ward,
            "search": search
        },
        "hotspots": hotspots
    }

@app.get("/api/hotspots/summary")
def get_topology_summary():
    """
    Returns official hydrological network breakdown & 80/20 Pareto principle statistics:
    32 critical trunk choke points account for 81.0% of systemic flood risk.
    """
    return topology_service.get_summary()

@app.get("/api/hotspots/corridors")
def get_corridors():
    """
    Returns GIS polylines, discharge ratings, and bottleneck confluences
    for Gurugram's 3 master drainage corridors (Leg 1, Leg 2, Leg 3).
    """
    return {
        "corridors": topology_service.get_corridors()
    }

@app.get("/api/hotspots/{spot_id}")
def get_hotspot_detail(spot_id: str):
    """
    Lookup a specific hotspot by ID (e.g. 'hs_grg_001') or Code (e.g. 'GRG-001').
    """
    spot = topology_service.get_hotspot_by_id(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail=f"Hotspot '{spot_id}' not found in 159-node topology.")
    return spot

@app.post("/api/predict")
def predict_single(req: PredictionRequest):
    """
    Sub-millisecond inference for custom storm telemetry.
    Returns risk probability, predicted depth with 95% Confidence Interval.
    """
    try:
        result = predict_hotspot_risk(
            rainfall_mm_hr=req.rainfall_mm_hr,
            cumulative_3h_rain_mm=req.cumulative_3h_rain_mm,
            elevation_m=req.elevation_m,
            catchment_area_sqkm=req.catchment_area_sqkm,
            drain_silt_pct=req.drain_silt_pct,
            pump_deployed=req.pump_deployed,
            critical_infra_proximity=req.critical_infra_proximity
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predict/hotspots")
def predict_all_hotspots(
    rain_mm_hr: float = 35.0,
    tier: Optional[int] = None,
    leg: Optional[str] = None,
    pareto_only: bool = False,
    pump_active_spot: Optional[str] = None,
    limit: Optional[int] = None
):
    """
    Vectorized batch inference across Gurugram 159 vulnerability hotspots.
    Executes in <5ms, dynamically calculating 95% Confidence Intervals,
    continuous water depth, and lead-time SOP recommendations.
    """
    t0 = time.perf_counter()
    hotspots = topology_service.get_all_hotspots(
        tier=tier,
        leg=leg,
        pareto_only=pareto_only
    )

    if limit is not None and limit > 0:
        hotspots = hotspots[:limit]

    pump_set = {pump_active_spot.strip()} if pump_active_spot else set()
    results = predict_hotspots_batch(
        hotspots=hotspots,
        rainfall_mm_hr=rain_mm_hr,
        cumulative_3h_rain_mm=rain_mm_hr * 1.8,
        pump_active_spot_ids=pump_set
    )
    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)

    critical_count = sum(1 for r in results if r["prediction"]["risk_tier"] in ("CRITICAL", "CRITICAL_RISK"))
    watch_count = sum(1 for r in results if r["prediction"]["risk_tier"] in ("WATCH", "WATCH_ALERT"))
    safe_count = sum(1 for r in results if r["prediction"]["risk_tier"] in ("LOW_RISK", "SAFE"))

    return {
        "rainfall_mm_hr": rain_mm_hr,
        "inference_latency_ms": latency_ms,
        "total_hotspots_evaluated": len(results),
        "status_breakdown": {
            "critical_risk_nodes": critical_count,
            "watch_alert_nodes": watch_count,
            "safe_nodes": safe_count
        },
        "filters": {
            "tier": tier,
            "leg": leg,
            "pareto_only": pareto_only,
            "pump_active_spot": pump_active_spot
        },
        "hotspots": results
    }

# ------------------ SOP & POLITICAL DEFENSIBILITY ENDPOINTS (DELIVERABLE 3) ------------------
@app.get("/api/sop/status")
def get_sop_status():
    """
    Returns the real-time operational status of the 4-phase MCG Pre-Event SOP protocol
    (T-24H Radar Watch, T-12H High-Ground Staging, T-6H Sump Drawdown, T-2H Boom Barriers).
    """
    return sop_service.get_sop_status()

@app.post("/api/sop/checkoff")
def checkoff_sop_task(req: SopCheckoffRequest):
    """
    Allows Junior Engineers (JE) or Executive Engineers (XEN) to log an SOP completion
    with digital verification timestamp.
    """
    try:
        return sop_service.checkoff_sop_task(
            sop_id=req.sop_id,
            verified_by=req.verified_by,
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/sop/auto-trigger")
def auto_trigger_sop(req: AutoTriggerRequest):
    """
    Evaluates real-time rainfall intensity (mm/hr) and triggers lead-time SOP phases automatically.
    """
    return sop_service.auto_trigger_by_rainfall(req.rain_mm_hr)

@app.get("/api/sop/whatsapp-payload/{sop_id}")
def get_whatsapp_work_order(sop_id: str):
    """
    Generates bilingual (Hindi + English) WhatsApp and SMS work order payloads
    formatted for instant field officer dispatch.
    """
    try:
        return sop_service.generate_je_whatsapp_payload(sop_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/sop/public-commitment-board")
def get_public_commitment_board():
    """
    Public-facing immutable audit ledger of pre-positioned pumps and flood prevention proofs.
    Cryptographically signed using HMAC-SHA256 to prove actions were taken prior to storm onset.
    """
    entries = sop_service.get_public_commitment_board()
    return {
        "commitment_count": len(entries),
        "audit_protocol": "HMAC-SHA256 MUNICIPAL INTEGRITY SEAL",
        "entries": entries
    }

@app.post("/api/sop/commitment")
def log_public_commitment(req: PublicCommitmentRequest):
    """
    Logs a new tamper-evident staging record on the Public Commitment Board.
    """
    return sop_service.log_commitment_entry(
        location_code=req.location_code,
        location_name=req.location_name,
        predicted_depth_cm=req.predicted_depth_cm,
        actual_depth_cm=req.actual_depth_cm,
        mitigation_liters_lakh=req.mitigation_liters_lakh,
        staged_asset=req.staged_asset,
        summary=req.summary
    )

@app.get("/api/fleet/status")
def get_fleet_telematics():
    """
    Returns live telematics for the 2-Ring Fleet Architecture:
    Ring-A (80% Trunk Locked) and Ring-B (20% Ward & RWA Flex Buffer).
    """
    return sop_service.get_fleet_status()

@app.post("/api/fleet/dispatch")
def dispatch_fleet_vehicle(req: FleetDispatchRequest):
    """
    Enforces the Algorithmic RWA Geofence Lock.
    Rejects diversion of Ring-A Super Suckers away from the 32 Pareto choke points
    unless authorized by Commissioner Dual-Key Override. Automatically redirects
    diverted requests to Ring-B.
    """
    try:
        return sop_service.request_fleet_dispatch(
            vehicle_id=req.vehicle_id,
            target_location=req.target_location,
            requestor=req.requestor,
            is_vip_request=req.is_vip_request,
            override_token=req.override_token
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/fleet/dual-key-override")
def issue_dual_key_override(req: DualKeyOverrideRequest):
    """
    Generates a cryptographically signed Commissioner Dual-Key Override token
    and logs the transaction into the Public RTI audit ledger.
    """
    return sop_service.generate_commissioner_override(
        reason=req.reason,
        authorized_by=req.authorized_by
    )

# ------------------ VANDAL-PROOF SENSOR & GeM CAPEX ENDPOINTS (DELIVERABLE 4) ------------------
@app.get("/api/sensor/capex-model")
def get_sensor_gem_capex():
    """
    Returns the authoritative Indian Government e-Marketplace (GeM) Capex budget (₹49.14 Lakhs)
    and 5-Year Annual Maintenance Contract (AMC) projection for Gurugram's 159-hotspot sensor mesh.
    """
    return sensor_service.get_gem_capex_model()

@app.get("/api/sensor/telemetry")
def get_sensor_telemetry():
    """
    Returns real-time network-wide telemetry across all 3 tiers:
    36 Tier-1 Ultrasonics, 83 Tier-2 CCTV Virtual Stencils, 40 Tier-3 SI Check-ins, 16 ARGs, 8 Gateways.
    """
    return sensor_service.get_sensor_telemetry_status()

@app.post("/api/sensor/tamper-alert")
def simulate_sensor_tamper(req: SensorTamperRequest):
    """
    Demonstrates zero-data-loss anti-vandalism failover:
    When an overhead 4mm MS cage tamper switch trips, telemetry fails over to
    redundant SS316 mechanical float switches and GMDA ICCC CCTV optical curb stencils.
    """
    return sensor_service.simulate_anti_vandalism_tamper(req.node_code)

@app.post("/api/sensor/reset-tamper")
def reset_sensor_tamper(req: SensorTamperRequest):
    """
    Resets the tamper switch alarm after security inspection.
    """
    return sensor_service.reset_sensor_tamper(req.node_code)

@app.get("/api/sensor/gateways")
def get_sensor_gateways():
    """
    Returns IN865 outdoor LoRaWAN gateway health and secured gated compound ARG telemetry.
    """
    return {
        "gateways": sensor_service._gateways,
        "gated_args": sensor_service._gated_args
    }

# -------------------------------------------------------------------------
# STEP 5: CITIZEN & B2B HYPERLOCAL ALERT CHANNELS (DELIVERABLE 5)
# -------------------------------------------------------------------------
@app.post("/api/alert/generate-sms")
def generate_offline_sms(req: SmsGenerationRequest):
    """
    Generates a standard 7-bit GSM compliant SMS string strictly <= 160 bytes.
    Enables emergency rescue SOS during total 4G/5G mobile tower blackout or low-bandwidth 2G.
    """
    try:
        return alert_service.generate_emergency_sms(
            lat=req.lat,
            lng=req.lng,
            hotspot_code=req.hotspot_code,
            depth_cm=req.depth_cm,
            req_type=req.req_type,
            battery_pct=req.battery_pct
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/alert/parse-sms")
def parse_inbound_sms(req: SmsParseRequest):
    """
    Parses an incoming raw 160-byte SMS, validates its CRC16-CCITT checksum,
    and registers an emergency disaster dispatch record in the control room.
    """
    try:
        return alert_service.parse_emergency_sms(req.raw_sms)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/alert/mesh-relay")
def simulate_mesh_relay(req: MeshRelayRequest):
    """
    Simulates multi-hop P2P mesh relay across gridlocked vehicles during total cellular blackout.
    Uses BLE 5.0 and Wi-Fi Direct ad-hoc hops until reaching an SDRF command unit.
    """
    return alert_service.simulate_mesh_relay(
        origin_lat=req.origin_lat,
        origin_lng=req.origin_lng,
        hotspot_code=req.hotspot_code,
        incident_type=req.incident_type,
        distress_text=req.distress_text
    )

@app.get("/api/alert/ivr-bulletin/{option_id}")
def get_ivr_bulletin(option_id: int):
    """
    Synthesizes bilingual voice audio bulletins in both Hindi (हिंदी) and Haryanvi (हरियाणवी)
    accessible from any basic ₹800 keypad phone via Toll-Free 1800-180-1817.
    """
    try:
        return alert_service.get_ivr_bulletin(option_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/alert/ivr-sos")
def submit_ivr_voice_sos(req: IvrSosRequest):
    """
    Ingests an emergency voice SOS logged from a basic keypad phone via Toll-Free 1800-180-1817 (Option 4).
    Automatically creates an urgent dispatch ticket for SDRF rescue boat crews.
    """
    return alert_service.submit_ivr_voice_sos(
        caller_phone=req.caller_phone,
        spoken_location=req.spoken_location,
        spoken_emergency=req.spoken_emergency,
        dialect=req.dialect,
        passengers_count=req.passengers_count
    )

@app.get("/api/alert/b2b/cyberhub")
def get_b2b_cyberhub_status():
    """
    Returns real-time status of the DLF Cyber City & Cyber Hub subterranean flood containment protocol:
    Stage (T-60m to T-15m), hydraulic flood barriers (+1.2m), and DHBVN 11kV electrical isolation.
    """
    return alert_service.get_b2b_cyberhub_status()

@app.post("/api/alert/b2b/countdown")
def advance_b2b_countdown(req: CyberHubCountdownRequest):
    """
    Advances the automated B2B flood escalation countdown (T-60m to T-15m)
    to demonstrate automatic barrier deployment and 11kV electrical grid cutoff.
    """
    return alert_service.advance_b2b_cyberhub_countdown(req.target_minutes)

@app.post("/api/alert/b2b/acknowledge")
def acknowledge_b2b_protocol(req: CyberHubAckRequest):
    """
    Logs an official facility manager compliance acknowledgment proving that flood barriers
    and 11kV electrical power isolation were verified before catastrophic inundation.
    """
    return alert_service.acknowledge_b2b_protocol(
        facility_manager_id=req.facility_manager_id,
        company=req.company,
        phase_code=req.phase_code,
        verification_token=req.verification_token
    )

@app.get("/api/model/metadata")
def get_model_metadata():
    """Returns explainability statistics & feature importances for civic judges"""
    meta_path = os.path.join(backend_dir, "ml", "models", "model_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Metadata not found")

# Serve the static frontend index.html & index.11.html
project_root = os.path.dirname(backend_dir)
index_html_path = os.path.join(project_root, "index.html")
index_11_path = os.path.join(project_root, "index.11.html")
manifest_path = os.path.join(project_root, "manifest.json")
service_worker_path = os.path.join(project_root, "service-worker.js")
core_js_path = os.path.join(project_root, "jalrakshak_core.js")
logo_png_path = os.path.join(project_root, "logo.png")
logo_jpg_path = os.path.join(project_root, "logo.jpg")
city_bg_path = os.path.join(project_root, "city_bg_render.jpg")

@app.get("/logo.png")
def serve_logo_png():
    if os.path.exists(logo_png_path):
        return FileResponse(logo_png_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="logo.png not found")

@app.get("/logo.jpg")
def serve_logo_jpg():
    if os.path.exists(logo_jpg_path):
        return FileResponse(logo_jpg_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="logo.jpg not found")

@app.get("/city_bg_render.jpg")
def serve_city_bg():
    if os.path.exists(city_bg_path):
        return FileResponse(city_bg_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="city_bg_render.jpg not found")

@app.get("/login-bg.jpg")
def serve_login_bg():
    if os.path.exists(city_bg_path):
        return FileResponse(city_bg_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="login-bg.jpg not found")

@app.get("/manifest.json")
def serve_manifest():
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="manifest.json not found")

@app.get("/service-worker.js")
def serve_service_worker():
    if os.path.exists(service_worker_path):
        return FileResponse(
            service_worker_path,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"}
        )
    raise HTTPException(status_code=404, detail="service-worker.js not found")

@app.get("/jalrakshak_core.js")
def serve_core_js():
    if os.path.exists(core_js_path):
        return FileResponse(core_js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="jalrakshak_core.js not found")

@app.get("/")
def serve_index():
    if os.path.exists(index_html_path):
        return FileResponse(index_html_path)
    return {"message": "JalRakshak NCR API online. index.html not found."}

@app.get("/index.html")
def serve_index_direct():
    if os.path.exists(index_html_path):
        return FileResponse(index_html_path)
    return FileResponse(index_11_path)

@app.get("/index.11.html")
def serve_index11():
    if os.path.exists(index_11_path):
        return FileResponse(index_11_path)
    return FileResponse(index_html_path)

@app.get("/jalrakshak_ncr_ai_flood_management_system.html")
def serve_jalrakshak_legacy():
    legacy_path = os.path.join(project_root, "jalrakshak_ncr_ai_flood_management_system.html")
    if os.path.exists(legacy_path):
        return FileResponse(legacy_path)
    return FileResponse(index_html_path)

if __name__ == "__main__":
    import uvicorn
    print("=" * 65)
    print("  NeerNetra | JalRakshak NCR Backend & Explainable ML Server")
    print("=" * 65)
    print("  * Web Dashboard: http://127.0.0.1:8000")
    print("  * OpenAPI / Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=backend_dir)
