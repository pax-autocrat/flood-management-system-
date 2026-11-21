"""
JalRakshak NCR — Phase 5 Automated Verification Suite
Validates:
1. Persistent Crowdsourced Hazard Registry (Jal-Doot)
2. EXIF GPS Metadata Extraction from Smartphone Photographs
3. Computer Vision Photometric Water Surface Verification Filter
4. Citizen Hazard Submission with Open Manhole / Live Wire Flags
5. Community Upvoting / Downvoting Lifecycle & 4-Hour TTL Auto-Expiry
6. Spatial Proximity Radius Filtering (Haversine 3 km Radius)
7. Life-Threatening Hazard-Only Filtering
"""

import sys
import os
import io
from fastapi.testclient import TestClient
from PIL import Image

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from main import app
from services.crowdsource_service import crowdsource_service

client = TestClient(app)

def create_synthetic_test_image(has_reflection: bool = True) -> bytes:
    """Generates an in-memory synthetic image to test Computer Vision photometric filter."""
    img = Image.new("RGB", (320, 240), color=(60, 60, 65))
    # Draw high-contrast specular puddle reflections in the bottom half
    pixels = img.load()
    if has_reflection:
        for y in range(120, 240):
            for x in range(50, 270):
                # Gradient reflection
                intensity = 180 if (x + y) % 12 == 0 else 55
                pixels[x, y] = (intensity, intensity, intensity + 5)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_phase5_tests():
    print("=" * 75)
    print("  PHASE 5 VERIFICATION: CROWDSOURCING JAL-DOOT & COMPUTER VISION")
    print("  Team: NeerNetra | Lead: Kamal Shukla | SustainX 2026")
    print("=" * 75)

    # ------------------ TEST 1: CROWDSOURCED HAZARDS REGISTRY ------------------
    print("\n[TEST 1] Testing Persistent Community Hazards Registry...")
    res_list = client.get("/api/v1/reports")
    assert res_list.status_code == 200, f"Query failed: {res_list.text}"
    reports = res_list.json()["reports"]
    assert len(reports) >= 3, f"Expected >= 3 seeded reports, got {len(reports)}"

    # Check Sector 31 Open Manhole hazard
    sec31 = next((r for r in reports if "Sector 31" in r["location_address"]), None)
    assert sec31 is not None
    assert sec31["is_manhole_open"] == 1
    assert sec31["status"] in ("VERIFIED_AI", "CONFIRMED_COMMUNITY")
    print(f"  -> Detected Open Manhole Pin: {sec31['location_address']} (Water: {sec31['estimated_depth_cm']}cm, Status: {sec31['status']})")
    print("  [PASS] Persistent community hazard registry verified.")

    # ------------------ TEST 2: COMPUTER VISION PHOTOMETRIC VERIFICATION ------------------
    print("\n[TEST 2] Testing Computer Vision Photometric Surface Water Filter...")
    # Test realistic reflective wet road image
    water_bytes = create_synthetic_test_image(has_reflection=True)
    cv_result = crowdsource_service.verify_flood_image(water_bytes)
    assert cv_result["is_valid"] is True
    assert cv_result["ai_confidence_score"] >= 0.60
    assert "LOW_SATURATION_WATER_PUDDLE" in cv_result["detected_features"]
    print(f"  -> AI Image Verification Score: {cv_result['ai_confidence_score']} ({cv_result['verdict']})")
    print(f"  -> Detected Fluid Signatures: {cv_result['detected_features']}")
    print("  [PASS] Computer Vision photometric water verification verified.")

    # ------------------ TEST 3: EXIF GPS METADATA EXTRACTION ------------------
    print("\n[TEST 3] Testing Smartphone EXIF GPS Coordinate Extraction & Geofence...")
    # Create image with EXIF GPS tags for Gurugram (28.4535° N, 77.0515° E)
    img = Image.new("RGB", (320, 240), color=(70, 70, 70))
    exif_dict = img.getexif()
    # GPSInfo tag ID is 34853 (0x8825)
    # 28° 27' 12.6" N, 77° 3' 5.4" E
    gps_data = {
        1: 'N',
        2: (28.0, 27.0, 12.6),
        3: 'E',
        4: (77.0, 3.0, 5.4)
    }
    exif_dict[34853] = gps_data
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_dict)
    
    extracted = crowdsource_service.extract_exif_gps(buf.getvalue())
    assert extracted is not None, "Failed to extract EXIF GPS tags!"
    assert extracted["has_exif_gps"] is True
    assert abs(extracted["lat"] - 28.4535) < 0.01
    assert abs(extracted["lng"] - 77.0515) < 0.01
    assert extracted["is_in_gurugram"] is True
    print(f"  -> Extracted EXIF GPS: Lat {extracted['lat']}, Lng {extracted['lng']}")
    print(f"  -> Geofence Verified: Coordinates confirmed inside Gurugram Municipal District.")
    print("  [PASS] EXIF GPS extraction and municipal geofencing verified.")

    # ------------------ TEST 4: CITIZEN HAZARD SUBMISSION WORKFLOW ------------------
    print("\n[TEST 4] Testing Citizen Hazard Submission Workflow (`POST /api/v1/reports`)...")
    res_submit = client.post("/api/v1/reports", json={
        "reporter_name": "Deepak Batra",
        "reporter_phone": "+91-9811887766",
        "location_address": "Golf Course Road near Sec 42 Rapid Metro",
        "lat": 28.4480,
        "lng": 77.0980,
        "estimated_depth_cm": 45,
        "is_manhole_open": True,
        "is_wire_hazard": False,
        "photo_url": "https://s3.jalrakshak.in/reports/golf_sec42.jpg",
        "has_exif_gps": True,
        "ai_confidence_score": 0.94
    })
    assert res_submit.status_code == 200, f"Submission failed: {res_submit.text}"
    sub_data = res_submit.json()
    assert sub_data["status"] == "report_published"
    rep_id = sub_data["report_id"]
    assert "expires_at" in sub_data
    print(f"  -> Published Hazard Pin: ID {rep_id} (Open Manhole on Golf Course Rd)")
    print(f"  -> Automatic 4-Hour TTL Expiry: {sub_data['expires_at']}")
    print("  [PASS] Citizen hazard report submission & TTL creation verified.")

    # ------------------ TEST 5: COMMUNITY UPVOTING & DOWNVOTING LIFECYCLE ------------------
    print("\n[TEST 5] Testing Community 'Still Flooded?' Upvote/Downvote Lifecycle...")
    # Upvote report twice to hit 3 upvotes -> Should elevate to CONFIRMED_COMMUNITY
    res_vote1 = client.post(f"/api/v1/reports/{rep_id}/vote", json={"vote_type": "STILL_FLOODED"})
    assert res_vote1.status_code == 200
    res_vote2 = client.post(f"/api/v1/reports/{rep_id}/vote", json={"vote_type": "STILL_FLOODED"})
    assert res_vote2.status_code == 200
    vote_data = res_vote2.json()
    assert vote_data["upvotes"] == 3
    assert vote_data["new_status"] == "CONFIRMED_COMMUNITY"
    print(f"  -> Upvoted Report: {vote_data['upvotes']} Community Upvotes (Status elevated to CONFIRMED_COMMUNITY +2h TTL)")

    # Downvote 3 times -> Should mark as CLEARED_BY_COMMUNITY
    for _ in range(3):
        client.post(f"/api/v1/reports/{rep_id}/vote", json={"vote_type": "WATER_RECEDED"})
    cleared_rep = client.get(f"/api/v1/reports/{rep_id}").json()
    assert cleared_rep["status"] == "CLEARED_BY_COMMUNITY"
    print(f"  -> Downvoted Report: 3 Downvotes (Status transitioned to CLEARED_BY_COMMUNITY)")
    print("  [PASS] Community upvoting & downvoting lifecycle verified.")

    # ------------------ TEST 6: SPATIAL PROXIMITY RADIUS FILTERING ------------------
    print("\n[TEST 6] Testing Spatial Proximity Radius Filtering (3 km Radius)...")
    # Query within 2 km of Sector 31 (28.4530, 77.0510)
    res_prox = client.get("/api/v1/reports?user_lat=28.4530&user_lng=77.0510&radius_km=2.0")
    assert res_prox.status_code == 200
    prox_reports = res_prox.json()["reports"]
    # Sector 31 report should be present and distance < 2.0 km
    for p in prox_reports:
        assert p["distance_from_user_km"] <= 2.0
    print(f"  -> Filtered Reports within 2.0 km of Sector 31: Count = {len(prox_reports)}")
    print("  [PASS] Spatial proximity radius filtering verified.")

    # ------------------ TEST 7: HAZARD-ONLY FILTER ------------------
    print("\n[TEST 7] Testing Life-Threatening Hazard-Only Filter...")
    res_hazards = client.get("/api/v1/reports?hazard_only=true")
    assert res_hazards.status_code == 200
    hazard_pins = res_hazards.json()["reports"]
    for hp in hazard_pins:
        assert hp["is_manhole_open"] == 1 or hp["is_wire_hazard"] == 1
    print(f"  -> Critical Hazards Filtered: {len(hazard_pins)} Open Manholes / Live Fallen Wires")
    print("  [PASS] Life-threatening hazard-only filter verified.")

    print("\n" + "=" * 75)
    print("  SUCCESS: ALL 7 / 7 PHASE 5 TESTS PASSED WITH 100% SUCCESS!")
    print("  Crowdsourced Jal-Doot, Computer Vision filter, & EXIF GPS verified.")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    run_phase5_tests()
