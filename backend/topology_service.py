"""
NeerNetra - JalRakshak NCR
Drainage Topology & Hotspot Management Service (Deliverable 1)
High-performance in-memory indexing of Gurugram's 159 official flood hotspots,
3 drainage corridors, and 80/20 Pareto choke point calculations.
"""

import os
import json
from typing import List, Dict, Any, Optional

# Load authoritative dataset
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
HOTSPOTS_FILE = os.path.join(DATA_DIR, "hotspots_159.json")
SUMMARY_FILE = os.path.join(DATA_DIR, "hotspots_summary.json")

# Master Drainage Corridors (Leg 1, Leg 2, Leg 3)
DRAINAGE_CORRIDORS = [
    {
        "id": "LEG_3",
        "name": "LEG 3 (BADSHAHPUR MASTER TRUNK CONDUIT)",
        "description": "Aravalli / Ghata Check Dam → Badshahpur Stream → Subhash Chowk → Rajiv Chowk → Hero Honda Chowk → Khandsa Box Culvert → Narsinghpur Sink → Najafgarh Outfall",
        "color": "#4F46E5",
        "rated_capacity_cusecs": 2400,
        "critical_choke_point": "Khandsa Box Culvert & Hero Honda Underpass",
        "vulnerability_share_pct": 58.4,
        "coords": [
            [28.4110, 77.1210],  # Ghata Dam
            [28.3950, 77.0480],  # Badshahpur Village
            [28.4283, 77.0398],  # Subhash Chowk
            [28.4449, 77.0345],  # Rajiv Chowk Underpass
            [28.4265, 77.0031],  # Hero Honda Chowk
            [28.4180, 76.9910],  # Khandsa Box Culvert
            [28.4024, 76.9796],  # Narsinghpur Highway Sink
            [28.4610, 76.9740],  # Basai Outfall
            [28.4980, 76.9550]   # Najafgarh Confluence
        ]
    },
    {
        "id": "LEG_2",
        "name": "LEG 2 (CENTRAL SPINE & OLD GURUGRAM CONDUIT)",
        "description": "DLF Cyber City / Shankar Chowk → IFFCO Chowk → Sector 14 Main Drain → Sheetla Mata Road → Atul Kataria Chowk → Palam Vihar / Bajghera → Najafgarh Drain",
        "color": "#0284C7",
        "rated_capacity_cusecs": 1300,
        "critical_choke_point": "Sheetla Mata Road & Atul Kataria Chowk",
        "vulnerability_share_pct": 26.2,
        "coords": [
            [28.5020, 77.0860],  # Shankar Chowk
            [28.4773, 77.0689],  # IFFCO Chowk Metro
            [28.4710, 77.0420],  # Sector 14 Confluence
            [28.4754, 77.0315],  # Sheetla Mata Road Sump
            [28.4852, 77.0450],  # Atul Kataria Chowk
            [28.5140, 77.0220],  # Bajghera Underpass
            [28.5180, 77.0050]   # Najafgarh Reach
        ]
    },
    {
        "id": "LEG_1",
        "name": "LEG 1 (EAST CORRIDOR / GOLF COURSE SPINE)",
        "description": "Aravalli Foothills / Gwal Pahari → Sector 56 Terminus → Golf Course Road Underpasses (Sec 27/42/54) → Sikanderpur Interchange → DLF Phase 1-5 Trunk",
        "color": "#10B981",
        "rated_capacity_cusecs": 1100,
        "critical_choke_point": "Golf Course Road Underpass & Sikanderpur Junction",
        "vulnerability_share_pct": 15.4,
        "coords": [
            [28.4280, 77.1420],  # Gwal Pahari
            [28.4320, 77.1060],  # Sector 56 Culvert
            [28.4480, 77.1030],  # Genpact Chowk
            [28.4575, 77.0968],  # Golf Course Road Sec 27
            [28.4815, 77.0925],  # Sikanderpur Interchange
            [28.4946, 77.0888]   # Belvedere / DLF Phase 3
        ]
    }
]

class TopologyService:
    def __init__(self):
        self._hotspots: List[Dict[str, Any]] = []
        self._id_index: Dict[str, Dict[str, Any]] = {}
        self._code_index: Dict[str, Dict[str, Any]] = {}
        self._summary: Dict[str, Any] = {}
        self.load_data()

    def load_data(self):
        """Loads canonical 159 hotspots dataset and constructs fast lookup hash tables"""
        if os.path.exists(HOTSPOTS_FILE):
            with open(HOTSPOTS_FILE, "r", encoding="utf-8") as f:
                self._hotspots = json.load(f)
        else:
            raise FileNotFoundError(f"Authoritative dataset missing: {HOTSPOTS_FILE}")

        if os.path.exists(SUMMARY_FILE):
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                self._summary = json.load(f)

        self._id_index = {h["id"]: h for h in self._hotspots}
        self._code_index = {h["code"].upper(): h for h in self._hotspots}

    def get_all_hotspots(
        self,
        tier: Optional[int] = None,
        leg: Optional[str] = None,
        pareto_only: bool = False,
        ward: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query 159 hotspots with multi-dimensional filtering for control room dashboards.
        """
        results = self._hotspots

        if tier is not None:
            results = [h for h in results if h["tier"] == tier]

        if leg is not None:
            leg_query = leg.upper().strip()
            results = [h for h in results if leg_query in h["leg_id"] or leg_query in h["leg"].upper()]

        if pareto_only:
            results = [h for h in results if h.get("is_pareto_choke_point", False)]

        if ward is not None:
            results = [h for h in results if h.get("ward") == ward]

        if search:
            q = search.lower().strip()
            results = [
                h for h in results
                if q in h["name"].lower()
                or q in h["code"].lower()
                or q in h.get("critical_infra", "").lower()
                or q in h.get("bypass_route", "").lower()
            ]

        return results

    def get_hotspot_by_id(self, spot_id: str) -> Optional[Dict[str, Any]]:
        """O(1) lookup by hotspot ID or Code (e.g. 'hs_grg_001' or 'GRG-001')"""
        clean_id = spot_id.strip()
        if clean_id in self._id_index:
            return self._id_index[clean_id]
        clean_code = clean_id.upper()
        if clean_code in self._code_index:
            return self._code_index[clean_code]
        return None

    def get_summary(self) -> Dict[str, Any]:
        """Returns topology statistics and Pareto summary metrics"""
        return self._summary

    def get_corridors(self) -> List[Dict[str, Any]]:
        """Returns geospatial GIS polylines for the 3 master drainage corridors"""
        return DRAINAGE_CORRIDORS


# Singleton instance for high-throughput zero-copy access
topology_service = TopologyService()
