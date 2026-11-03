import asyncio
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import httpx
from app.main import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health
        r = await client.get("/api/health")
        print("1. Health Check:", r.status_code, r.json())
        assert r.status_code == 200

        # 2. Weather
        r = await client.get("/api/weather/live")
        w = r.json()
        print(f"2. Live Weather: {w['temperature']}°C, {w['rain_mm_hr']} mm/hr, {w['alert_level']}")
        assert r.status_code == 200

        # 3. Hotspots
        r = await client.get("/api/hotspots")
        spots = r.json()
        print(f"3. Hotspots: {len(spots)} retrieved. Top spot: {spots[0]['name']} ({spots[0]['current_depth_cm']} cm)")
        assert len(spots) == 8

        # 4. KPIs
        r = await client.get("/api/hotspots/kpis/summary")
        kpis = r.json()
        print(f"4. KPIs Summary: Road Safety={kpis['road_safety_pct']}%, Desilted={kpis['desilted_ratio']}")
        assert r.status_code == 200

        # 5. Fleet
        r = await client.get("/api/fleet")
        vehicles = r.json()
        print(f"5. Emergency Fleet: {len(vehicles)} units loaded")
        assert len(vehicles) == 8

        # 6. SOS Queue
        r = await client.get("/api/sos")
        sos_list = r.json()
        print(f"6. SOS Queue: {len(sos_list)} active distress tickets")
        assert len(sos_list) >= 3

        # 7. Safe Route Calculation
        r = await client.post("/api/routes/calculate", json={
            "origin_key": "loc_cyberhub",
            "dest_key": "loc_sohna",
            "travel_mode": "FOUR_WHEELER"
        })
        route = r.json()
        print(f"7. Route Calculation: {route['origin_name']} -> {route['dest_name']} ({route['safe_eta']})")
        assert r.status_code == 200

        print("\nALL 7 ASYNC REST ENDPOINTS TESTED & PASSED!")

if __name__ == "__main__":
    asyncio.run(run_tests())
