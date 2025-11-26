# Sprint 4 — Virus App Foundation

This project sets up the base for Sprint 4. It has a simple Flask server and a small Python client.

## Server
- Endpoint: `/api/report`
- Accepts JSON POST
- Validates fields: `machine_id`, `timestamp`, `event`, `data`
- Logs each payload into `reports.log`

Run:
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server/app.py
