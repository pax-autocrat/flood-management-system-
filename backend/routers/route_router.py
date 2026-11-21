"""
JalRakshak NCR — Flood-Aware Spatial Routing Router (Phase 4)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from services.routing_service import routing_service
from services.geocoding_service import geocoding_service

router = APIRouter(prefix="/api/v1/route", tags=["Navigation & Spatial Routing"])

class RouteCalculationRequest(BaseModel):
    origin: List[float] = Field(..., description="[Latitude, Longitude] of origin point", min_length=2, max_length=2)
    destination: List[float] = Field(..., description="[Latitude, Longitude] of destination point", min_length=2, max_length=2)
    travel_mode: str = Field(default="FOUR_WHEELER", description="Mode: 'FOUR_WHEELER', 'TWO_WHEELER', 'ON_FOOT', 'SUV', 'RESCUE_TRUCK'")
    weather_factor: float = Field(default=1.0, description="Active storm rain multiplier (0.18 normal, 0.52 ai, 1.0 storm)")

@router.post("/calculate")
def calculate_flood_safe_route(req: RouteCalculationRequest):
    """
    Computes flood-aware point-to-point route.
    Penalizes road segments exceeding vehicle wading limits and generates
    safe green corridor with turn-by-turn maneuvers and elevation profile.
    """
    valid_modes = ("FOUR_WHEELER", "TWO_WHEELER", "ON_FOOT", "SUV", "RESCUE_TRUCK")
    if req.travel_mode.upper() not in valid_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid travel_mode '{req.travel_mode}'. Must be one of {valid_modes}"
        )

    return routing_service.calculate_flood_route(
        origin_lat=req.origin[0],
        origin_lng=req.origin[1],
        dest_lat=req.destination[0],
        dest_lng=req.destination[1],
        travel_mode=req.travel_mode,
        weather_factor=req.weather_factor
    )

@router.get("/search")
def search_gurugram_places(q: str = Query(..., description="Search query: sector, hospital, market, or landmark")):
    """
    Geocoding autocomplete search for Gurugram sectors and landmarks.
    """
    results = geocoding_service.search_places(q)
    return {
        "query": q,
        "count": len(results),
        "places": results
    }

@router.get("/landmarks")
def list_standard_landmarks():
    """
    Returns standard curated Gurugram landmarks for route selection dropdowns.
    """
    return {
        "landmarks": geocoding_service.get_all_landmarks()
    }
