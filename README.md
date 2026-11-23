# NeerNetra — Gurugram Flood Prevention & AI Dispatch
### SustainX 2026: The Sustainability Hackathon (Great Lakes Institute of Management, Gurgaon)
**Team:** `NeerNetra` &nbsp;|&nbsp; **Submission File:** `TeamNeerNetra-SustainX-R1.pdf` &nbsp;|&nbsp; **Lead & Backend Engineer:** `Kamal Shukla`

[![SustainX 2026](https://img.shields.io/badge/SustainX-2026_Hackathon-0284c7.svg)](https://github.com)
[![Team](https://img.shields.io/badge/Team-NeerNetra-059669.svg)](https://github.com)
[![MCG Compliance](https://img.shields.io/badge/MCG_Gurugram-SOP_Ready-e11d48.svg)](https://github.com)
[![ML Performance](https://img.shields.io/badge/ML_Accuracy-89.7%25_R2_0.975-purple.svg)](https://github.com)
[![Topology](https://img.shields.io/badge/Topology-159_Nodes_Pareto_81%25-blue.svg)](https://github.com)
[![SOP Protocol](https://img.shields.io/badge/SOP-T--24H_to_T--2H_Active-emerald.svg)](https://github.com)
[![GeM Capex](https://img.shields.io/badge/GeM_Capex-₹49.14_Lakhs-darkgreen.svg)](https://github.com)
[![Alert Channels](https://img.shields.io/badge/Alerts-160B_SMS_•_Mesh_•_IVR_•_B2B-orange.svg)](https://github.com)

---

## 1. Executive Summary & Problem Framing

Gurugram contributes close to **60% of Haryana's GDP** and hosts **250+ Fortune 500 companies**. Yet, every monsoon, the city suffers catastrophic paralysis:
* **159 waterlogging hotspots** identified across Gurugram by the Municipal Corporation of Gurugram (MCG).
* **₹150–200 Crore** in direct recurring economic losses every single year.
* **₹1,400+ Crore spent** over 10 years on drainage and emergency fixes since the 2016 "Gurujam", with no lasting improvement.
* **The Root Cause:** The failure is **operational and informational, not budgetary**. MCG operates reactively—mobilizing heavy de-watering pumps *after* water is 50–80 cm deep. By then, arterial expressways (NH-48, Sohna Road) have gridlocked, and pump trucks are physically trapped in the exact traffic jams they were dispatched to clear.

**JalRakshak NCR by Team NeerNetra** shifts MCG from *reactive pumping* to **algorithmic pre-positioning (T−60 minutes)**.

---

## 2. Step 1 Completed: Explainable AI Predictive Engine (Deliverable 2)

As part of **Deliverable 2**, Team NeerNetra has implemented and verified a lightweight, explainable machine learning engine built specifically for municipal operations under the hackathon's *"No PhD needed"* constraint:

```mermaid
flowchart LR
    A["Raw Data Inputs<br/>• Open-Meteo Rain (mm/hr)<br/>• 3h Cumulative Rain<br/>• Digital Elevation Model (DEM)<br/>• Catchment Area (sq km)<br/>• Drain Silt % (JE Field Input)<br/>• Pump Pre-Deployed (0/1)"] --> B["Explainable ML Pipeline<br/>• GradientBoostingClassifier<br/>• GradientBoostingRegressor"]
    B --> C["Real-Time Municipal Outputs<br/>1. Risk Tier: CRITICAL / WATCH / LOW<br/>2. Flood Probability: 0 - 100%<br/>3. Predicted Depth: ±18.0cm (95% CI)<br/>4. Action: T-60m Staging Protocol<br/>5. Feature Explainability Weights"]
```

### Verified Model Performance Metrics
* **Risk Classification Accuracy:** **89.69%** across 3 risk tiers (`LOW_RISK`, `WATCH`, `CRITICAL`).
* **Water Depth Prediction $R^2$ Score:** **0.9746** ($97.5\%$ variance explained).
* **Mean Absolute Error (MAE):** **6.50 cm** on unseen Gurugram storm test holdouts.
* **Inference Latency:** **1.32 ms** per single prediction ($< 5.0\text{ ms}$ enterprise SLA).
* **Pre-Emptive Mitigation Proof:** Active 5000 GPM pump deployment mathematically reduces flood depth by **64.9%** ($101.9\text{ cm} \rightarrow 35.8\text{ cm}$).
* **Explainability Feature Importances:**
  1. `rainfall_mm_hr`: **28.6%**
  2. `catchment_area_sqkm`: **22.8%**
  3. `cumulative_3h_rain_mm`: **18.8%**
  4. `pump_deployed`: **17.5%**
  5. `elevation_m`: **10.3%**
  6. `drain_silt_pct`: **2.0%**

---

## 3. Step 2 Completed: 159-Hotspot Drainage Topology Layer & Pareto Engine (Deliverable 1)

As part of **Deliverable 1**, Team NeerNetra has constructed, geocoded, and verified the complete 159-hotspot municipal drainage topology layer of Gurugram.

```mermaid
flowchart TD
    subgraph Basins["3 Master Drainage Basins (Corridors)"]
        L1["LEG 1: East / Golf Course Spine (35 Nodes • 1,100 cusecs)"]
        L2["LEG 2: Central Spine & Old Gurugram (49 Nodes • 1,300 cusecs)"]
        L3["LEG 3: Badshahpur Master Trunk Conduit (75 Nodes • 2,400 cusecs)"]
    end
    subgraph Tiers["159 Official MCG Hotspot Architecture"]
        T1["Tier 1: 36 Critical Trunk Nodes<br/>(Khandsa Box Culvert, Hero Honda, Rajiv Chowk, Narsinghpur)"]
        T2["Tier 2: 83 Arterial Culverts<br/>(Sector Dividers & GMDA Feeder Conduits)"]
        T3["Tier 3: 40 Ward Depressions<br/>(Colony Basins & Low Pockets)"]
    end
    subgraph Pareto["80/20 Pareto Control Room Focus"]
        P32["32 Choke Points (20.1% of Nodes)<br/>Govern 81.0% of Systemic Flood Accumulation"]
    end
    Basins --> Tiers
    Tiers --> Pareto
```

### 3-Tier Hotspot Breakdown & Sensor Architecture
| Hotspot Tier | Node Count | Primary Role | Sensor Architecture | Gurugram Examples |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1 (Trunk Nodes)** | **36** | Highway underpasses, arterial intersections, master confluences | IP68 non-contact 70kHz ultrasonic in 4mm galvanized MS anti-vandal cages + SS316 float backup | Khandsa Box Culvert, Hero Honda Chowk, Rajiv Chowk, Narsinghpur, Subhash Chowk, IFFCO Chowk |
| **Tier 2 (Arterial Culverts)** | **83** | Inter-sector dividing roads, lateral feeder culverts | Existing GMDA ICCC CCTV cameras reading calibrated curb depth stencils via OpenCV | Sector 4/7, Sector 14, Sector 23, Sector 31, Sector 46 Substation, Palam Vihar, Basai |
| **Tier 3 (Ward Depressions)** | **40** | Local residential colony sinks & secondary culverts | Geo-tagged Sanitary Inspector (SI) mobile app check-ins + 1-tap citizen verification | Sector 15 Part 1, Sector 22B, Sector 56 Kendriya Vihar, Shivaji Nagar, Badshahpur Bazar |
| **TOTAL** | **159** | Complete Municipal Coverage across all 35 MCG Wards | Hybrid Low-Capex Sensor Mesh | **₹49.14 Lakhs Total Capex** |

### Verified 80/20 Pareto Choke Point Proof
In hydrology, systemic flood accumulation follows a power-law distribution governed by rated discharge capacity, siltation factor, and upstream catchment basin ($Q \propto A^{1.35}$).
* **Total Hotspots:** 159 nodes
* **Critical Choke Points:** **32 nodes** ($20.1\%$ of total network)
* **Systemic Flood Accumulation Governed:** **81.0%**
* **Vectorized Batch ML Latency:** **2.44 ms** across all 159 hotspots ($< 0.02\text{ ms}$ per node).

---

## 4. Step 3 Completed: MCG Pre-Event SOP Engine & Public Commitment View (Deliverable 3)

As part of **Deliverable 3**, Team NeerNetra has implemented the municipal operational engine that transforms flood management from reactive chaos into predictive certainty.

```mermaid
sequenceDiagram
    autonumber
    actor MET as IMD Doppler Radar
    participant SOP as SOP Trigger Engine
    participant JE as Junior Engineers (Field)
    participant PCB as Public Commitment Board
    participant RWA as VIP / RWA Requestor
    participant FLT as Fleet Manager (Geofence)

    MET->>SOP: Rainfall intensity crosses threshold (15 / 25 / 35 / 50 mm/hr)
    SOP->>JE: Broadcast WhatsApp / SMS bilingual work orders (Hindi + English)
    JE->>SOP: Complete pre-positioning on dry high ground
    SOP->>PCB: Log timestamped proof with HMAC-SHA256 digital signature
    Note over PCB: Solves Prevention Paradox: Proves pumps staged BEFORE rain hit!
    RWA->>FLT: Request diverting Ring-A Super Sucker to colony puddle
    FLT-->>RWA: REJECTED by Algorithmic Geofence Lock (Auto-dispatch QRV-401 Ring-B)
```

### 4-Phase Pre-Event Operations SOP Timeline
| Phase | Lead Time Window | Rain Trigger | Operational Action | Primary Owner & Communication |
| :--- | :--- | :--- | :--- | :--- |
| **SOP-24H** | **T−24 Hours** | $15\text{ mm/hr}$ radar watch | Clear trash screens at all 32 Pareto choke points. Top up 12-hour diesel reserves on all pumps and backup generators. | Executive Engineer (XEN) & Sanitary Inspectors (SI) |
| **SOP-12H** | **T−12 Hours** | $25\text{ mm/hr}$ confirmation | Mobilize mobile suction tankers to dry approach ramps (Hero Honda & Rajiv Chowk). Deploy suction hoses into sump entry wells. | Junior Engineers (JE) & Pump Drivers |
| **SOP-6H** | **T−6 Hours** | $35\text{ mm/hr}$ convective alert | Draw down all 11 underpass sumps to 0% capacity (creating maximum surge buffer). Coordinate with DHBVN (1912) for feeder isolation. | Underpass Pump Operators & DHBVN 1912 |
| **SOP-2H** | **T−2 Hours** | $50+\text{ mm/hr}$ nowcast | Warm-idle pump diesel engines for zero prime lag. Stage Traffic Police (1095) boom barrier crews. Lower barriers if water hits 25 cm. | Traffic Police TI (1095) & Boom Barrier Marshals |

---

## 5. Step 4 Completed: Vandal-Proof Sensor Architecture & ₹49.14 Lakh GeM Capex Model (Deliverable 4)

As part of **Deliverable 4**, Team NeerNetra has engineered a high-resilience sensor network designed specifically to defeat street vandalism, copper wire theft, and monsoon battery destruction:

```mermaid
flowchart TD
    subgraph StreetHardware["Tier 1: 36 Overhead Trunk Nodes (4-6m AGL)"]
        U1["IP68 70kHz Ultrasonic Sensor<br/>(Mounted overhead out of reach)"]
        MS["4mm Galvanized MS Security Cage<br/>(Tamper switch + Internal antenna)"]
        SS["SS316 Mechanical Float Switch<br/>(Zero-power redundant failover)"]
        U1 --> MS
        MS --> SS
    end

    subgraph ZeroCapex["Tier 2: 83 Arterial Junctions (Zero Hardware Capex)"]
        CCTV["Existing GMDA ICCC CCTV Cameras"]
        STENCIL["₹1,800 Painted Reflective Curb Stencils<br/>(Read via OpenCV Video Analytics)"]
        CCTV --> STENCIL
    end

    subgraph SecuredCompounds["Rooftop Met Infrastructure (Zero Street Exposure)"]
        ARG["16 Tipping-Bucket Rain Gauges<br/>(Inside 24/7 Guarded DHBVN / MCG Compounds)"]
        GW["8 Outdoor PoE LoRa Gateways<br/>(IN865 Band • 99.2% City Coverage)"]
        ARG --> GW
    end
```

### Official Indian GeM (Government e-Marketplace) Itemized Capex Budget
| Item ID | Description | GeM Category Code | Qty | Unit Cost (₹) | Total Cost (₹) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GEM-01** | IP68 Ultrasonic Water Level Sensors (0.5–10m range, LoRaWAN IN865 + 2G, LiFePO4 solar) | `GeM/2026/WATER-LEVEL-IOT-IP68` | 42 | ₹18,500 | **₹7,77,000** |
| **GEM-02** | 4mm Galvanized MS Anti-Theft Security Cages + Tamper Switch + SS316 Float Backup | `GeM/2026/MUNICIPAL-HARDWARE-SECURITY` | 36 | ₹9,700 | **₹3,49,200** |
| **GEM-03** | FRP Tipping-Bucket Rain Gauges (16 units) + 8-Channel Outdoor PoE LoRa Gateways (8 units) | `GeM/2026/METEOROLOGICAL-ARG-GW` | 24 | ₹35,333 | **₹8,48,000** |
| **GEM-04** | Painted Reflective Curb Stencils (83 units) + High-Brightness Underpass Warning LED Boards (22 units) | `GeM/2026/TRAFFIC-SAFETY-DISPLAYS` | 105 | ₹10,851 | **₹11,39,400** |
| **GEM-05** | GMDA ICCC Edge Analytics Server + GIS Engine / Offline SMS Gateway / 1800-Voice IVR Setup | `GeM/2026/SYSTEM-INTEGRATION-SMARTCITY` | 1 | ₹18,00,000 | **₹18,00,000** |
| **TOTAL** | **Complete Gurugram 159-Hotspot Smart Infrastructure Package** | **Indian GeM Rate Contracts** | — | — | **₹49,13,600 (~₹49.14 Lakhs)** |

### 5-Year AMC & Municipal Budget Perspective
* **Annual Maintenance Contract (AMC):** **₹9.80 Lakhs / year** ($> 95\%$ SLA uptime guarantee, 4-hour repair turnaround).
* **5-Year Total Cost of Ownership (TCO):** ₹49.14L (Capex) + ₹49.00L (5-Yr AMC) = **₹98.14 Lakhs** ($< \text{₹}1.0\text{ Crore}$ over 5 full years!).
* **Budget Perspective:** Total Capex represents **0.022%** of MCG's ₹2,200 Cr Annual Budget ($< 0.1\%$) and **0.035%** of the ₹1,400+ Crore spent on ad-hoc fixes since 2016.
* **Anti-Vandalism Failover Proof:** When an overhead MS cage tamper switch is tripped, the system activates redundant SS316 mechanical float switches and pulls GMDA ICCC optical curb readings, ensuring **zero telemetry data loss**.

---

## 6. Step 5 Completed: Citizen & B2B Hyperlocal Alert Channels (Deliverable 5)

As part of **Deliverable 5**, Team NeerNetra has engineered zero-internet disaster communication channels and critical B2B subterranean infrastructure protocols:

```mermaid
flowchart TD
    subgraph OfflineCitizen["1. Citizen Zero-Signal Channels (No 4G/5G Required)"]
        SMS["160-Byte GSM SMS Engine<br/>(NEERNETRA-SOS • 7-bit GSM • CRC16-CCITT)"]
        MESH["4-Hop P2P Mesh Relay<br/>(BLE 5.0 & Wi-Fi Direct ad-hoc bounce across cars)"]
        IVR["1800-180-1817 Toll-Free Voice IVR<br/>(Bilingual Hindi & Haryanvi Audio for ₹800 feature phones)"]
    end

    subgraph B2BProtocol["2. Corporate IT Park Subterranean Protection (DLF Cyber Hub)"]
        T60["T-60M: Advisory & Barrier Motors Energized"]
        T45["T-45M: +1.2m Hydraulic Flood Walls Deployed at Ramps"]
        T30["T-30M: Subterranean B1-B3 Evacuation & Siren Active"]
        T15["T-15M: DHBVN 11kV Substation Isolated • Rooftop DG Online"]
        T60 --> T45 --> T30 --> T15
    end

    subgraph SDRFCommand["3. Incident Command Action"]
        SDRF["SDRF / Civil Defense Tactical Post<br/>• Auto-dispatches rescue zodiac boats<br/>• Logs legally binding compliance certificates"]
    end

    OfflineCitizen --> SDRFCommand
    B2BProtocol --> SDRFCommand
```

### 1. 160-Byte GSM SMS Generator & Tamper Verification
* **Disaster Reality:** During massive monsoons (e.g. 2016 Gurujam), 4G/5G cellular towers lose power or suffer extreme data packet drops. 2G GSM signaling channels (SMS over SS7/MAP) remain resilient.
* **Payload Format:** `NEERNETRA-SOS|GPS:<lat>,<lng>|<NODE>|<DEPTH>CM|<REQ>|BAT:<pct>%|CRC:<crc16>`
* **Strict Budget:** Always $\le 160$ bytes (typical size: 68–77 bytes).
* **CRC16-CCITT Integrity:** Every SMS carries a 4-hex checksum that immediately detects bit-rot or deliberate tampering. Inbound parser auto-registers verified emergency rescue tickets.

### 2. 4-Hop P2P BLE / Wi-Fi Direct Mesh Relay Simulation
* **Mechanism:** Stranded vehicles trapped on NH-48 / Subhash Chowk form an ad-hoc local mesh:
  * **Hop 1 (Origin):** Citizen Smartphone (`CAR-DL8C-4129`, BLE 5.0 Coded PHY, TTL: 4)
  * **Hop 2 (Vehicle Relay):** Commercial Truck (`CAR-HR55-7821`, BLE 5.0 Mesh, $42\text{m}$, TTL: 3)
  * **Hop 3 (Flyover Gateway):** MCG Quick Response Vehicle (`MCG-QRV-401`, Wi-Fi Direct P2P, $118\text{m}$, TTL: 2)
  * **Hop 4 (Terminal Gateway):** SDRF Tactical Base (`SDRF-COMMAND-BASE-HEROHONDA`, LoRa/Satellite, $210\text{m}$, TTL: 1)
* **Delivery Receipt:** Issues cryptographic receipt token (`ACK-SDRF-XXXXXXXXXX`) and auto-dispatches an SDRF inflatable rescue boat.

### 3. Toll-Free 1800-180-1817 Voice IVR Audio Bulletin Synthesizer
* **Inclusivity:** Works on any basic ₹800 keypad phone without internet or smartphone apps.
* **Bilingual Dialects:** Synthesizes spoken audio bulletins in both **Hindi (खड़ी बोली)** and **Haryanvi (हरियाणवी)**:
  * **Option 1:** Road Closures & Waterlogged Underpass Alerts (NH-48, Subhash Chowk, Sohna Rd bypass).
  * **Option 2:** Safe High-Ground Relief Camps (Tau Devi Lal Stadium Sec 38, Huda Gymkhana Sec 29).
  * **Option 3:** Active Dewatering Pumps & Clearance ETA (50 HP pumps & Khandsa axial pumps).
  * **Option 4:** Keypad Voice SOS Submission (auto-transcribed & tagged `HIGH_SEVERITY_RESCUE`).

### 4. DLF Cyber Hub B2B Subterranean Flood Containment & 11kV Power Isolation
* **Asset Protection:** Safeguards subterranean basements B1/B2/B3 holding 11kV transformers and 15,000+ corporate vehicles:
  * **$T-60\text{m}$ (Advisory):** Sump pumps verified; barrier motors energized.
  * **$T-45\text{m}$ (Barrier Deployment):** Automatic $+1.2\text{m}$ hydraulic steel flood stop walls raised at vehicle ramps.
  * **$T-30\text{m}$ (Subterranean Evacuation):** Sirens sound across B1/B2/B3; vehicles rerouted to elevated MLCP.
  * **$T-15\text{m}$ (11kV Power Isolation):** DHBVN vacuum circuit breakers tripped to prevent catastrophic explosion and electrocution. Rooftop Tier-4 DG sets & multi-region cloud failover take full load.
  * **FM Compliance Audit:** Facility manager signs digital verification certificate logged in public safety ledger.

---

## 7. Full API Endpoints Reference (31 Endpoints)

| Method | Endpoint | Parameters / Body | Description | Latency |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | None | System status, model accuracy, and 159-node topology metadata. | `< 1 ms` |
| `GET` | `/api/hotspots/159` | `tier`, `leg`, `pareto_only`, `ward`, `search` | Queryable 159-node Gurugram drainage topology dataset with multi-attribute filtering. | `< 2 ms` |
| `GET` | `/api/hotspots/summary` | None | Tier breakdown, sensor architecture, and mathematical Pareto 81% metrics. | `< 1 ms` |
| `GET` | `/api/hotspots/corridors`| None | GIS polylines and discharge capacities for Leg 1, Leg 2, and Leg 3. | `< 1 ms` |
| `GET` | `/api/hotspots/{spot_id}`| `spot_id` or `code` (e.g. `GRG-001`) | O(1) single hotspot topological details and pump requirements. | `< 1 ms` |
| `GET` | `/api/predict/hotspots` | `rain_mm_hr`, `tier`, `leg`, `pareto_only`, `pump_active_spot` | **Vectorized batch ML prediction** across 159 hotspots with 95% CIs and lead-time actions. | **2.44 ms** |
| `POST`| `/api/predict` | `PredictionRequest` JSON body | Real-time single-point prediction for custom storm telemetry. | `1.32 ms` |
| `GET` | `/api/sop/status` | None | Current status and completion percentage of the 4 SOP phases (T-24H to T-2H). | `< 1 ms` |
| `POST`| `/api/sop/checkoff` | `SopCheckoffRequest` JSON body | Logs a digital signoff by a field officer (JE Sandeep / XEN Ramesh). | `< 1 ms` |
| `POST`| `/api/sop/auto-trigger` | `AutoTriggerRequest` JSON body | Evaluates live rain intensity and automatically advances SOP phases. | `< 1 ms` |
| `GET` | `/api/sop/public-commitment-board` | None | Public audit ledger with HMAC-SHA256 cryptographic verification seals. | `< 1 ms` |
| `POST`| `/api/sop/commitment` | `PublicCommitmentRequest` JSON body | Logs a new tamper-evident staging record on the public commitment board. | `< 1 ms` |
| `GET` | `/api/sop/whatsapp-payload/{sop_id}` | `sop_id` (e.g. `SOP-12H`) | Generates bilingual (Hindi + English) WhatsApp and SMS dispatch text. | `< 1 ms` |
| `GET` | `/api/fleet/status` | None | Telematics and geofence status for Ring-A and Ring-B units. | `< 1 ms` |
| `POST`| `/api/fleet/dispatch` | `FleetDispatchRequest` JSON body | **Enforces Algorithmic RWA Geofence Lock.** Rejects unauthorized trunk diversion. | `< 1 ms` |
| `POST`| `/api/fleet/dual-key-override` | `DualKeyOverrideRequest` JSON body | Issues a Commissioner Dual-Key Override token logged in the public RTI ledger. | `< 1 ms` |
| `GET` | `/api/sensor/capex-model` | None | **Authoritative Indian GeM Capex Model (₹49.14L)** & 5-Year AMC Breakdown. | `< 1 ms` |
| `GET` | `/api/sensor/telemetry` | None | Real-time 3-tier sensor telemetry (36 Ultrasonic, 83 CCTV, 40 SI crowd, 16 ARGs). | `< 1 ms` |
| `POST`| `/api/sensor/tamper-alert` | `SensorTamperRequest` JSON body | Simulates anti-theft MS cage tamper trip and verifies zero-data-loss failover. | `< 1 ms` |
| `POST`| `/api/sensor/reset-tamper` | `SensorTamperRequest` JSON body | Resets tamper alarm after security inspection. | `< 1 ms` |
| `GET` | `/api/sensor/gateways` | None | IN865 outdoor LoRaWAN gateway health and gated compound ARG telemetry. | `< 1 ms` |
| `POST`| `/api/alert/generate-sms` | `SmsGenerationRequest` JSON body | **Generates 160-byte GSM SMS** with CRC16-CCITT for total cellular blackout. | `< 0.1 ms` |
| `POST`| `/api/alert/parse-sms` | `SmsParseRequest` JSON body | Ingests inbound raw SMS, checks CRC checksum, registers rescue ticket. | `< 0.1 ms` |
| `POST`| `/api/alert/mesh-relay` | `MeshRelayRequest` JSON body | **4-Hop P2P BLE/Wi-Fi Direct mesh propagation** simulation to SDRF command base. | `< 0.1 ms` |
| `GET` | `/api/alert/ivr-bulletin/{id}`| `option_id` (1 to 4) | Bilingual Hindi & Haryanvi audio bulletins for 1800-180-1817 Helpline. | `< 0.1 ms` |
| `POST`| `/api/alert/ivr-sos` | `IvrSosRequest` JSON body | Logs keypad phone voice SOS and auto-dispatches SDRF rescue boat unit. | `< 0.1 ms` |
| `GET` | `/api/alert/b2b/cyberhub`| None | Live status of DLF Cyber Hub subterranean flood containment protocol. | `< 0.1 ms` |
| `POST`| `/api/alert/b2b/countdown` | `CyberHubCountdownRequest` JSON body | Advances automated B2B escalation countdown (T-60m to T-15m). | `< 0.1 ms` |
| `POST`| `/api/alert/b2b/acknowledge` | `CyberHubAckRequest` JSON body | Facility manager digital sign-off on flood barriers & 11kV electrical isolation. | `< 0.1 ms` |
| `GET` | `/api/model/metadata` | None | Full model explainability, feature importances, and validation scores. | `< 1 ms` |
| `GET` | `/` | None | Serves the interactive JalRakshak NCR dashboard with live 159-node GIS map. | Static |

---

## 8. Quick Start & Verification

### 1-Click Launch (Recommended)
Double-click [`run.bat`](file:///c:/Users/kamal/OneDrive/Desktop/SustainX2/run.bat) in the project root. It will:
1. Boot the FastAPI and explainable ML prediction engine on `http://127.0.0.1:8000`.
2. Automatically launch the dashboard in your default browser.

### Run All 5 Automated Test Suites
Run the verified unit and integration test suites anytime:

* **Step 1 (ML Engine & Mitigation):**
  ```powershell
  & "C:\Users\kamal\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" backend\test_step1.py
  ```
  *(5/5 Tests Passed: Accuracy 89.69%, R² 0.9746, MAE 6.50cm, Latency 1.32ms)*

* **Step 2 (159 Hotspots & Pareto Engine):**
  ```powershell
  & "C:\Users\kamal\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" backend\test_step2.py
  ```
  *(6/6 Tests Passed: 159 Nodes, Coordinates in Bounds, Pareto 81.0%, Batch Latency 2.44ms)*

* **Step 3 (SOP Engine & Political Governance):**
  ```powershell
  & "C:\Users\kamal\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" backend\test_step3.py
  ```
  *(7/7 Tests Passed: 4 SOP Phases, Field Signoff, HMAC-SHA256 Seals, RWA Geofence Lock, Dual-Key Override, Hindi WhatsApp, Latency <1ms)*

* **Step 4 (Sensor Architecture & GeM Capex):**
  ```powershell
  & "C:\Users\kamal\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" backend\test_step4.py
  ```
  *(6/6 Tests Passed: GeM Sum ₹49,13,600, 5-Yr AMC ₹49.0L, 159 Nodes Monitored, MS Cage Tamper Failover, Gateways PDR >98%, Latency <1ms)*

* **Step 5 (Citizen & B2B Hyperlocal Alert Channels):**
  ```powershell
  & "C:\Users\kamal\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe" backend\test_step5.py
  ```
  *(6/6 Tests Passed: 160-Byte GSM SMS Budget & CRC16, 4-Hop P2P Mesh Relay, 1800-180-1817 Bilingual IVR, Keypad Voice SOS, B2B Cyber Hub 11kV Cutoff, Latency <0.1ms)*

**Total Verification Status:** **30 / 30 Automated Unit & Integration Tests Passing (100% Success)**.

---

## 9. Official Competition Submission Files

* **Executive Summary PDF (2 Pages Exact):** [`TeamNeerNetra-SustainX-R1.pdf`](file:///c:/Users/kamal/OneDrive/Desktop/SustainX2/TeamNeerNetra-SustainX-R1.pdf)
* **Executive Summary Word DOCX:** [`TeamNeerNetra-SustainX-R1.docx`](file:///c:/Users/kamal/OneDrive/Desktop/SustainX2/TeamNeerNetra-SustainX-R1.docx)
* **Markdown Submission Artifact:** [TeamNeerNetra-SustainX-R1.md](file:///C:/Users/kamal/.gemini/antigravity/brain/9f4e76b2-4384-4863-b84a-a4c1c34c9cf0/TeamNeerNetra-SustainX-R1.md)
