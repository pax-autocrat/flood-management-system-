# JalRakshak NCR — Real-Time Civic Flood Management & Rescue Platform

**SustainX 2026 Innovation Prototype**

JalRakshak NCR is a real-time flood monitoring, rescue coordination, and flood-aware navigation platform for Gurugram and the National Capital Region (NCR). It provides role-based workspaces for both Local Civilians and Municipal Corporation of Gurugram (MCG) Officials.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11+ with [FastAPI](https://fastapi.tiangolo.com/) & Uvicorn
- **Database**: SQLite with SQLAlchemy ORM (`backend/jalrakshak.db`)
- **Real-Time Telemetry**: WebSockets (`/api/fleet/ws/live-gps`) for vehicle GPS transponders
- **Live Weather**: Integrated with Open-Meteo AWS & simulated IMD Gurugram rainfall scenarios
- **Frontend**: Tailwind CSS, Leaflet Maps with Google Tiles, FontAwesome, Vanilla JS

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ installed (e.g. via `uv`, `py`, or standard Python installer).

### 2. Virtual Environment Setup & Dependencies
```powershell
# Navigate to the backend folder
cd backend

# Create virtual environment (if not already created)
uv venv .venv
# or: python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Start the Backend Server
```powershell
# From the backend folder
python run.py
# or: uvicorn app.main:app --reload --port 8000
```

Once running:
- **Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check |
| `POST` | `/api/auth/login` | Civilian / MCG Official authentication & role capabilities |
| `GET` | `/api/weather/live` | Live Gurugram weather telemetry & alerts |
| `POST` | `/api/weather/scenario` | Toggle simulation presets (`normal`, `ai`, `storm`) |
| `POST` | `/api/weather/sync` | Live sync from Open-Meteo AWS |
| `GET` | `/api/hotspots` | Gurugram flood hotspots with real-time computed depth |
| `GET` | `/api/hotspots/kpis/summary`| Road safety %, desilted ratio, active SOS count |
| `PATCH`| `/api/hotspots/{id}/drain` | Mark drain cleaned (reduces depth by 40%) vs clogged |
| `GET` | `/api/fleet` | Emergency vehicles (Tankers, Ambulances, Boats, QRVs) |
| `PATCH`| `/api/fleet/{id}/status` | Mark vehicle `OPEN` (Ready) or `OCCUPIED` |
| `POST` | `/api/fleet/{id}/dispatch`| Dispatch unit to a flooded hotspot or coordinate |
| `WS` | `/api/fleet/ws/live-gps` | WebSocket streaming live GPS transponder updates |
| `GET` | `/api/sos` | Distress queue with caller details & locations |
| `POST` | `/api/sos` | Submit emergency citizen distress request |
| `POST` | `/api/sos/{id}/assign` | Assign available emergency unit to distress call |
| `POST` | `/api/routes/calculate` | Flood-aware green bypass route vs red flooded route |

---

## 📂 Project Structure

```
SustainX2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, static mounting, CORS
│   │   ├── config.py            # App settings & Gurugram coordinates
│   │   ├── database.py          # SQLite engine & session maker
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── seed_data.py         # Seed dataset (8 hotspots, 8 fleet, 3 SOS)
│   │   ├── services/
│   │   │   ├── weather_service.py # Weather calculations & Open-Meteo
│   │   │   ├── fleet_service.py   # Fleet dispatch & GPS drift simulation
│   │   │   └── routing_service.py # Flood-aware bypass routing
│   │   └── routers/
│   │       ├── auth.py          # Login & roles
│   │       ├── weather.py       # Weather endpoints
│   │       ├── hotspots.py      # Hotspots & drain status
│   │       ├── fleet.py         # Vehicles & WebSocket
│   │       ├── sos.py           # SOS queue & triage
│   │       └── routes.py        # Safe route calculation
│   ├── jalrakshak.db            # SQLite relational database
│   ├── requirements.txt         # Pinned Python package dependencies
│   ├── run.py                   # Server startup script
│   └── verify_services.py       # Backend verification script
├── index.html                   # Frontend UI with live backend integration
└── README.md                    # Project documentation
```
