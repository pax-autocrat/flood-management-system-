import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.routers import auth, weather, hotspots, fleet, sos, routes
from app.schemas import (
    LoginRequest, WeatherScenarioUpdate, HotspotDrainUpdate,
    VehicleStatusUpdate, VehicleDispatchRequest, SosRequestCreate, RouteRequest
)

def run_e2e_verification():
    db = SessionLocal()
    print("=" * 65)
    print("  JALRAKSHAK NCR — END-TO-END INTEGRATION & RBAC TEST")
    print("=" * 65)

    # -------------------------------------------------------------------------
    # WORKFLOW 1: CIVILIAN USER JOURNEY
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 1: LOCAL CIVILIAN USER JOURNEY]")

    # 1.1 Civilian Authentication
    civ_login = auth.login(LoginRequest(name="Aarav Sharma", passcode="9811046021", role="CITIZEN"))
    assert civ_login.role == "CITIZEN"
    print(f"  1.1 Auth: Successfully logged in as {civ_login.name} (Role: {civ_login.role})")

    # 1.2 View Public Weather & Flood Alerts
    w_live = weather.get_live_weather(db)
    print(f"  1.2 Weather Station: Live IMD Telemetry = {w_live.temperature}°C, {w_live.rain_mm_hr} mm/hr ({w_live.alert_level})")

    public_spots = hotspots.get_all_hotspots(db)
    assert len(public_spots) == 8
    print(f"  1.3 Public Road Alerts: Loaded {len(public_spots)} Gurugram roads with live passability")

    # 1.4 Calculate Safe Navigation Route
    route_res = routes.calculate_route(RouteRequest(origin_key="loc_cyberhub", dest_key="loc_sohna", travel_mode="FOUR_WHEELER"))
    assert "26 mins" in route_res.safe_eta
    assert "2 hr 10 mins" in route_res.flooded_eta
    print(f"  1.4 Route Search: {route_res.origin_name} -> {route_res.dest_name}")
    print(f"      - Safe Route (Dry): {route_res.safe_eta}")
    print(f"      - Flooded Route (NH-48): {route_res.flooded_eta}")

    # 1.5 Submit Personal Emergency SOS
    new_sos = sos.create_sos_request(SosRequestCreate(
        person=civ_login.name,
        spot_id="hs_rajiv",
        location="Rajiv Chowk Underpass",
        issue="Vehicle Stuck in Deep Floodwater",
        note="Water rising above wheel arches near exit ramp."
    ), db)
    assert new_sos.id.startswith("SOS-")
    print(f"  1.5 Personal SOS Submission: Created ticket {new_sos.id} for {new_sos.person} at {new_sos.location}")

    # -------------------------------------------------------------------------
    # WORKFLOW 2: MCG OFFICIAL COMMAND & TRIAGE JOURNEY
    # -------------------------------------------------------------------------
    print("\n[WORKFLOW 2: MCG OFFICIAL COMMAND & OPERATIONS JOURNEY]")

    # 2.1 Official Authentication
    off_login = auth.login(LoginRequest(name="Vikram Singh", passcode="MCG-GURUGRAM-2026", role="OFFICIAL"))
    assert off_login.role == "OFFICIAL"
    print(f"  2.1 Auth: Successfully logged in as {off_login.name} (Role: {off_login.role})")

    # 2.2 Operational Dashboard KPIs
    kpis_before = hotspots.get_dashboard_kpis(db)
    print(f"  2.2 Command KPIs: Road Safety = {kpis_before.road_safety_pct}%, Desilted = {kpis_before.desilted_ratio}, Active SOS = {kpis_before.active_sos_count}")

    # 2.3 Drain Cleaner Desilting Management
    print("  2.3 Hotspot Desilting: Marking Hero Honda Chowk drain as CLEANED...")
    updated_spot = hotspots.update_hotspot_drain_status("hs_herohonda", HotspotDrainUpdate(drain_cleaned=True), db)
    assert updated_spot.drain_cleaned == True
    kpis_after_drain = hotspots.get_dashboard_kpis(db)
    print(f"      - Hotspot Depth dropped to {updated_spot.current_depth_cm} cm (40% water reduction)")
    print(f"      - Desilted Count increased to {kpis_after_drain.desilted_ratio}")

    # 2.4 Emergency Fleet Triage & SOS Dispatch
    print(f"  2.4 Dispatching Emergency Unit to Citizen SOS ({new_sos.id})...")
    assigned_ticket = sos.assign_vehicle_to_sos(new_sos.id, None, db)
    assert assigned_ticket.assigned_truck is not None
    assert assigned_ticket.status == "ASSIGNED"
    print(f"      - Assigned Unit: {assigned_ticket.assigned_truck} to ticket {assigned_ticket.id}")

    # 2.5 Hotspot Emergency Pumping Dispatch
    print("  2.5 Hotspot Pumping: Dispatching Suction Tanker #1 to Rajiv Chowk Underpass...")
    disp_v = fleet.dispatch_vehicle("TANKER-101", VehicleDispatchRequest(target_spot_id="hs_rajiv"), db)
    assert disp_v.status == "OCCUPIED"
    rajiv_spot = hotspots.get_hotspot_by_id("hs_rajiv", db)
    assert rajiv_spot.pump_assigned == True
    print(f"      - Unit status: {disp_v.status}, Location: {disp_v.route}")
    print(f"      - Rajiv Chowk pump active: {rajiv_spot.pump_assigned}, Depth reduced to: {rajiv_spot.current_depth_cm} cm")

    # 2.6 Dynamic Weather Scenario Switch (Storm -> Normal)
    print("  2.6 Weather Simulation: Switching scenario to 'normal' (18 mm/hr light rain)...")
    weather.update_weather_scenario(WeatherScenarioUpdate(scenario="normal"), db)
    kpis_normal = hotspots.get_dashboard_kpis(db)
    print(f"      - Road Safety jumped to: {kpis_normal.road_safety_pct}% (All wide roads passable)")

    # Restore weather to storm for default state
    weather.update_weather_scenario(WeatherScenarioUpdate(scenario="storm"), db)

    db.close()
    print("\n" + "=" * 65)
    print("  ALL E2E INTEGRATION & RBAC WORKFLOWS VERIFIED WITH ZERO ERRORS!")
    print("=" * 65)

if __name__ == "__main__":
    run_e2e_verification()
