# SMARTSHELF

Smart supermarket inventory and expiration monitoring system built with FastAPI, PostgreSQL, MQTT and a React dashboard.

## Architecture

- **Frontend:** React + Vite, Recharts and Lucide icons
- **Backend:** FastAPI + SQLAlchemy
- **Database:** PostgreSQL 16
- **Messaging:** Eclipse Mosquitto MQTT
- **Simulation:** Python smart-shelf simulator

The project is configured as a local, centralized deployment on one PC. Docker Compose runs the database, MQTT broker, API and dashboard.

## Requirements

- Docker Desktop with Docker Compose
- A local `.env` file (see below)

## Configuration

Create a root `.env` file:

```env
POSTGRES_DB=smartshelf
POSTGRES_USER=smartshelf_user
POSTGRES_PASSWORD=replace_with_a_local_password
POSTGRES_PORT=5432
MQTT_PORT=1883
```

Do not commit `.env` or production credentials.

## Run the application

From the repository root:

```powershell
docker compose up -d --build
```

Open:

- Dashboard: http://localhost:5173
- FastAPI documentation: http://localhost:8000/docs
- API health: http://localhost:8000/health

Stop services:

```powershell
docker compose down
```

## Dashboard features

- Live overview metrics from `GET /api/dashboard/summary`
- Inventory by product, batch and shelf
- Stock receiving and quantity adjustments
- Product, batch and smart-shelf registration
- Expiration and stock alerts, including mark-as-read and resolve actions
- Inventory movement chart based on recorded inventory events
- Automatic data refresh every 30 seconds

The dashboard uses the existing FastAPI endpoints through the Vite development proxy. It does not connect directly to PostgreSQL.

## Database initialization

The SQL schema is in `database/smartshelf_schema.sql`. Initialize a fresh database using that script before starting the application for the first time. Existing Docker volumes retain their current database contents.

## MQTT simulator

Install simulator dependencies and run the simulator from the `simulator` directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The simulator connects to the local Mosquitto broker on port 1883.

## Notes

- The default Mosquitto configuration is intended for local development and allows anonymous connections. Do not expose it to an untrusted network.
- The frontend is currently configured as a Vite development server inside Docker. For production deployment, replace it with a static build served by a production web server.
- The dashboard displays data returned by the backend. Empty database tables will appear as empty states rather than fabricated sample data.
