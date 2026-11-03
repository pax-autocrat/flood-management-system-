from fastapi import APIRouter
from app.schemas import RouteRequest, RouteResponse
from app.seed_data import GURUGRAM_LANDMARKS
from app.services.routing_service import RoutingService

router = APIRouter(prefix="/routes", tags=["Flood-Aware Safe Routing"])

@router.get("/landmarks")
def get_landmarks():
    return GURUGRAM_LANDMARKS

@router.post("/calculate", response_model=RouteResponse)
def calculate_route(payload: RouteRequest):
    result = RoutingService.calculate_route(
        origin_key=payload.origin_key,
        dest_key=payload.dest_key,
        travel_mode=payload.travel_mode
    )
    return RouteResponse(**result)
