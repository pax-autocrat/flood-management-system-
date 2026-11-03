from typing import Dict, Any, List
from app.seed_data import GURUGRAM_LANDMARKS

class RoutingService:
    @staticmethod
    def calculate_route(origin_key: str, dest_key: str, travel_mode: str = "FOUR_WHEELER") -> Dict[str, Any]:
        origin = GURUGRAM_LANDMARKS.get(origin_key, GURUGRAM_LANDMARKS["loc_cyberhub"])
        dest = GURUGRAM_LANDMARKS.get(dest_key, GURUGRAM_LANDMARKS["loc_sohna"])

        # Safe Dry Waypoints via Golf Course Road & SPR (elevated wide corridors)
        safe_waypoints = [
            [origin["lat"], origin["lng"]],
            [28.4685, 77.0890],
            [28.4450, 77.0940],
            [dest["lat"], dest["lng"]]
        ]

        # Flooded Route Waypoints passing through Rajiv Chowk (NH-48 bottleneck)
        flooded_waypoints = [
            [origin["lat"], origin["lng"]],
            [28.4449, 77.0345],  # Rajiv Chowk Underpass
            [dest["lat"], dest["lng"]]
        ]

        # Mode ETAs
        if travel_mode == "TWO_WHEELER":
            safe_eta = "21 mins (Elevated Corridor)"
            flooded_eta = "1 hr 45 mins (Engine Stall Risk)"
            corridor_label = "ELEVATED SECTOR 27/43 LINK"
        elif travel_mode == "ON_FOOT":
            safe_eta = "38 mins (Dry Footbridge Route)"
            flooded_eta = "Submerged / Impassable"
            corridor_label = "PEDESTRIAN ELEVATED OVERPASS"
        else:  # FOUR_WHEELER
            safe_eta = "26 mins (Dry Wide Arterials)"
            flooded_eta = "2 hr 10 mins (Submerged Underpasses)"
            corridor_label = "WIDE 6-LANE GOLF COURSE RD / SPR"

        steps = [
            {
                "time": "START",
                "title": f"ORIGIN: {origin['name'].upper()}",
                "sub": "Verified dry entry point"
            },
            {
                "time": "SAFE CORRIDOR",
                "title": corridor_label,
                "sub": "Bypasses deep water at Rajiv Chowk & Hero Honda Chowk"
            },
            {
                "time": "ARRIVE",
                "title": f"DESTINATION: {dest['name'].upper()}",
                "sub": f"Estimated Travel Time: {safe_eta}"
            }
        ]

        return {
            "origin_name": origin["name"],
            "dest_name": dest["name"],
            "travel_mode": travel_mode,
            "safe_eta": safe_eta,
            "flooded_eta": flooded_eta,
            "safe_waypoints": safe_waypoints,
            "flooded_waypoints": flooded_waypoints,
            "steps": steps
        }
