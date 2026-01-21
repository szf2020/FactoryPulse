# FactoryPulse - IIoT OEE Analytics Platform

![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![Backend](https://img.shields.io/badge/backend-Django_Rest_Framework-092E20)
![Frontend](https://img.shields.io/badge/frontend-React_Vite-61DAFB)

## Project Overview

**FactoryPulse** is a specialized Industrial Internet of Things (IIoT) platform engineered to calculate and visualize **Overall Equipment Effectiveness (OEE)** in real-time.

In modern manufacturing, simply knowing if a machine is "on" or "off" is insufficient. This application solves the visibility gap by processing high-frequency telemetry from the shop floor to quantify exactly how effectively manufacturing equipment is utilized. It transforms raw sensor data into the three critical OEE benchmarks:

1.  **Availability:** Tracking unplanned downtime and stop events.
2.  **Performance:** Measuring actual production speed against ideal cycle times.
3.  **Quality:** Monitoring the ratio of good parts versus scrap/defects.

### The IIoT Ecosystem

This project serves as the cloud/server infrastructure for the **Open IoT Gateway Firmware**, a custom C++ embedded solution for ESP32 microcontrollers. Together, they form a complete end-to-end Industry 4.0 solution:

* **Edge Layer (Data Collection):** [Open-IoT-Gateway-Firmware](https://github.com/petry-dev/Open-IoT-Gateway-Firmware) - Handles signal acquisition, protocol translation, and MQTT publishing.
* **Server Layer (Data Processing):** **FactoryPulse** (This Repository) - Handles data ingestion, complex OEE logic, persistent storage, and visualization.

---

## Application Gallery

### 1. Operational Dashboard (The OEE Hub)
The central command center designed for plant managers. It aggregates data from all active lines to present a global OEE percentage, total energy consumption, and real-time production throughput against daily targets.

![Dashboard Overview](assets/dashboard-light.png)

### 2. Deep Telemetry Analysis
A granular view for maintenance engineers. This module correlates OEE losses with physical telemetry. It renders real-time amperage charts to help diagnose if performance drops are due to mechanical stress or operator delay. Shown here in **Dark Mode**.

![Machine Details](assets/machine-detail-dark.png)

### 3. Production Reports
A historical log interface allowing management to audit past production shifts, export efficiency metrics, and analyze long-term downtime trends.

![Reports View](assets/reports-dark.png)

### 4. Asset Registry
A centralized catalog of all provisioned industrial assets (Robotic Arms, CNC Centers, Hydraulic Presses), displaying real-time connection status.

![Machines List](assets/machines-list.png)

### 5. Secure Authentication
Enterprise-grade login interface utilizing JWT (JSON Web Tokens) for secure, stateless session management.

![Login Screen](assets/login-screen.png)

---

## System Architecture

The solution implements a scalable **Event-Driven Architecture**:

1.  **Data Acquisition:** The Edge Firmware publishes events (Cycle Complete, Scrap Detected, Machine Error) and telemetry (Amperage) to an MQTT Broker.
2.  **Ingestion Middleware:** A Python-based worker subscribes to `industry/+/io`. It performs edge detection on digital signals to distinguish between a valid production cycle and a false positive before writing to the database.
3.  **Backend Core (Django):** Acts as the single source of truth. It manages the relational model between Machines, Production Events, and Sensor Readings.
4.  **Frontend (React):** Consumes the API to provide an optimistic UI. It polls for fresh data to ensure operators see the machine state with sub-second latency.

---

## Technical Stack

### Backend
* **Framework:** Django 6.0 & Django REST Framework (DRF).
* **Language:** Python 3.10+.
* **Messaging:** MQTT Protocol via Paho Client (Optimized for unstable factory networks).
* **Authentication:** SimpleJWT (Stateless Token Authentication).
* **Database:** SQLite (Dev) / PostgreSQL (Production).

### Frontend
* **Core:** React.js (Vite Ecosystem).
* **Styling:** Tailwind CSS (Utility-first framework for responsive design).
* **State Management:** React Context API.
* **Visualization:** Chart.js & react-chartjs-2.
* **Internationalization:** i18n support for English, Portuguese, and Spanish.

---

## Installation & Setup Guide

### Prerequisites
* Node.js (v18+)
* Python (v3.10+)
* Mosquitto MQTT Broker (Local or Remote)

### 1. Backend Configuration

Navigate to the backend directory and set up the environment:

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database Setup
python manage.py migrate,
```

### Simulation Data (Optional)

If no physical hardware is connected, run the seed script to populate the database with demo machines and historical telemetry for OEE visualization:

```bash

python manage.py seed_data

```

### Start the Services

You will need two terminal windows running simultaneously:

### Terminal 1: Start the MQTT Ingestion Worker

```bash

python manage.py run_mqtt

```
### Terminal 2: Start the API Server

```bash

python manage.py runserver

```

### 2. Frontend Configuration

Open a new terminal and navigate to the frontend directory:

```bash

cd frontend

# Install dependencies
npm install

# Start Development Server
npm run dev

```
Access the application at http://localhost:5173.

## API Documentation

The backend exposes a RESTful API for integration:

- **POST** `/api/token/`  
  Authenticate and retrieve Access/Refresh tokens.

- **GET** `/api/machines/`  
  Retrieve a list of assets with their current OEE snapshot.

- **GET** `/api/machines/{device_id}/`  
  Retrieve detailed timeseries data (Amps) and event logs for a specific machine.

## License

This project is open-source and available under the [MIT License](LICENSE).