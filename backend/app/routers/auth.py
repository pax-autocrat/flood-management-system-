from fastapi import APIRouter
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    role = payload.role.upper()
    if role not in ["OFFICIAL", "CITIZEN"]:
        role = "OFFICIAL"

    user_name = payload.name.strip() or ("Vikram Singh" if role == "OFFICIAL" else "Aarav Sharma")

    return LoginResponse(
        name=user_name,
        role=role,
        message=f"Authenticated as {role}",
        token=f"token-{role.lower()}-{hash(user_name)}"
    )

@router.get("/roles")
def list_available_roles():
    return {
        "OFFICIAL": {
            "title": "MCG Official (Command & Operations)",
            "capabilities": [
                "Full Road Safety % Analytics",
                "Drain Cleaner Hotspot Desilting Management",
                "Pending Citizen SOS Queue Triage & Vehicle Dispatch",
                "Emergency Fleet Allocation & Transponder Control"
            ]
        },
        "CITIZEN": {
            "title": "Local Civilian (Public Safety)",
            "capabilities": [
                "Live Weather Station Telemetry",
                "Public Waterlogging & Safe Route Search",
                "Submit Personal GPS SOS Distress Alert",
                "Emergency Speed Dial Helplines"
            ]
        }
    }
