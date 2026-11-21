"""
JalRakshak NCR — Gurugram Geocoding & Sector Search Service (Phase 4)
Engineered for Team NeerNetra (SustainX 2026)
Provides authoritative sector, landmark, and hospital geocoding autocomplete
constrained to the Gurugram municipal bounding box [28.32°N - 28.55°N, 76.85°E - 77.15°E].
"""

import os
import sys
import httpx
from typing import Dict, List, Any, Optional

class GeocodingService:
    # Bounding Box for Gurugram Municipal District & NCR Extensions
    BBOX_MIN_LAT = 28.3200
    BBOX_MAX_LAT = 28.5500
    BBOX_MIN_LNG = 76.8500
    BBOX_MAX_LNG = 77.1500

    def __init__(self):
        # Comprehensive curated local registry of Gurugram sectors & major landmarks
        self._local_places = [
            {"id": "loc_cyberhub", "name": "DLF Cyber Hub", "category": "COMMERCIAL", "sector": "DLF Phase 2", "lat": 28.4946, "lng": 77.0888, "address": "DLF Cyber City, Sector 24, Gurugram, 122002"},
            {"id": "loc_iffco", "name": "IFFCO Chowk Metro Station", "category": "TRANSIT", "sector": "Sector 29", "lat": 28.4773, "lng": 77.0689, "address": "MG Road, Sector 29, Gurugram, 122001"},
            {"id": "loc_huda", "name": "Millennium City Centre (HUDA City Centre)", "category": "TRANSIT", "sector": "Sector 29", "lat": 28.4593, "lng": 77.0724, "address": "Sector 29, Gurugram, 122001"},
            {"id": "loc_sec29", "name": "Sector 29 Market & Leisure Valley", "category": "COMMERCIAL", "sector": "Sector 29", "lat": 28.4682, "lng": 77.0635, "address": "Sector 29 Food & Cultural Hub, Gurugram"},
            {"id": "loc_golf", "name": "Golf Course Road (Sec 27)", "category": "HIGHWAY", "sector": "Sector 27", "lat": 28.4575, "lng": 77.0968, "address": "Golf Course Road, DLF Phase 5, Gurugram, 122009"},
            {"id": "loc_golf_sec54", "name": "Golf Course Road (Sec 54)", "category": "HIGHWAY", "sector": "Sector 54", "lat": 28.4350, "lng": 77.1000, "address": "Golf Course Road near Rapid Metro Sec 54"},
            {"id": "loc_sec56", "name": "Sector 56 Huda Market", "category": "RESIDENTIAL", "sector": "Sector 56", "lat": 28.4230, "lng": 77.1025, "address": "Sector 56, Golf Course Extension Rd, Gurugram"},
            {"id": "loc_rajiv", "name": "Rajiv Chowk Underpass", "category": "HIGHWAY", "sector": "Sector 32/33", "lat": 28.4449, "lng": 77.0345, "address": "NH-48 Rajiv Chowk Junction, Gurugram, 122001"},
            {"id": "loc_sohna", "name": "Sohna Road (Subhash Chowk)", "category": "HIGHWAY", "sector": "Sector 47/48", "lat": 28.4283, "lng": 77.0398, "address": "Subhash Chowk, Sohna Road, Gurugram, 122018"},
            {"id": "loc_medanta", "name": "Medanta The Medicity Hospital", "category": "HEALTHCARE", "sector": "Sector 38", "lat": 28.4394, "lng": 77.0416, "address": "CH Bakhtawar Singh Rd, Sector 38, Gurugram, 122001"},
            {"id": "loc_herohonda", "name": "Hero Honda Chowk Underpass", "category": "HIGHWAY", "sector": "Sector 34/37", "lat": 28.4265, "lng": 77.0031, "address": "NH-48 Hero Honda Chowk, Gurugram, 122004"},
            {"id": "loc_narsinghpur", "name": "Narsinghpur Stretch (NH-48)", "category": "HIGHWAY", "sector": "Sector 35", "lat": 28.4024, "lng": 76.9796, "address": "Delhi-Jaipur Expressway, Narsinghpur, Gurugram"},
            {"id": "loc_spr", "name": "Southern Peripheral Road (SPR)", "category": "HIGHWAY", "sector": "Sector 70/71", "lat": 28.4120, "lng": 77.0720, "address": "SPR Arterial Corridor, Gurugram"},
            {"id": "loc_sheetla", "name": "Sheetla Mata Temple & Old Road", "category": "COMMUNITY", "sector": "Sector 5", "lat": 28.4754, "lng": 77.0315, "address": "Sheetla Mata Road, Sector 5, Old Gurugram"},
            {"id": "loc_sec14", "name": "Sector 14 Main Market", "category": "COMMERCIAL", "sector": "Sector 14", "lat": 28.4715, "lng": 77.0450, "address": "Sector 14 Commercial Complex, Gurugram"},
            {"id": "loc_sec31", "name": "Sector 31 Market", "category": "RESIDENTIAL", "sector": "Sector 31", "lat": 28.4530, "lng": 77.0510, "address": "Sector 31 Huda Market, Gurugram"},
            {"id": "loc_palamvihar", "name": "Palam Vihar Central Park", "category": "RESIDENTIAL", "sector": "Palam Vihar", "lat": 28.5020, "lng": 77.0340, "address": "Palam Vihar Pocket C, Gurugram, 122017"},
            {"id": "loc_ambience", "name": "Ambience Mall Gurugram", "category": "COMMERCIAL", "sector": "Sector 24", "lat": 28.5042, "lng": 77.0970, "address": "NH-48 Delhi-Gurugram Border, Gurugram, 122002"},
            {"id": "loc_fortis", "name": "Fortis Memorial Research Institute", "category": "HEALTHCARE", "sector": "Sector 44", "lat": 28.4580, "lng": 77.0735, "address": "Sector 44, opposite HUDA City Centre, Gurugram"},
            {"id": "loc_artemis", "name": "Artemis Hospital", "category": "HEALTHCARE", "sector": "Sector 51", "lat": 28.4345, "lng": 77.0875, "address": "Sector 51, Gurugram, 122001"}
        ]

    def search_places(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Searches curated Gurugram sector registry with prefix and substring matching."""
        q = query.strip().lower()
        if not q:
            return self._local_places[:limit]

        matches = []
        for p in self._local_places:
            if (q in p["name"].lower() or 
                q in p["sector"].lower() or 
                q in p["category"].lower() or 
                q in p["address"].lower()):
                matches.append(p)

        return matches[:limit]

    def get_place_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Lookup landmark by ID."""
        for p in self._local_places:
            if p["id"] == place_id:
                return p
        return None

    def get_all_landmarks(self) -> List[Dict[str, Any]]:
        """Returns standard landmarks for route selection dropdowns."""
        return self._local_places

geocoding_service = GeocodingService()
