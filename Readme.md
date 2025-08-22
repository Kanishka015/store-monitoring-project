# Store Monitoring System

A backend service that monitors whether restaurant stores are open (uptime) or closed (downtime) during their business hours. It checks store status at regular intervals, processes the data, and provides reports through a REST API.

---

## Features

- **Store Data Import:** Load restaurant data from CSV files into a SQLite database.
- **Timezone Handling:** Convert local business hours into UTC for consistent time data.
- **Uptime/Downtime Calculation:** Estimate store status between checks and calculate how long each store was open or closed.
- **Report Generation:** Create CSV reports showing uptime and downtime for the last hour, day, and week.
- **Async API:** Uses a trigger-and-check pattern for report generation, so clients don’t have to wait.

---

## Tech Stack

- **Python**
- **FastAPI** (REST API)
- **Pandas**
- **SQLite + SQLAlchemy**
- **Pytz** (timezone handling)
- **Uvicorn** (server)

---

## How to Run

### 1. Start the API Server

Run this command from the project root:

```
uvicorn store_monitoring.main:app --reload
```

Server will start at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### 2. Open API Docs

Go to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

This gives you an interactive page to test all APIs.

---

### 3. Generate a Report

- Open `POST /trigger_report`
- Click **Try it out** → **Execute**
- Copy the `report_id` from the response

---

### 4. Get the Report

- Open `GET /get_report`
- Paste the `report_id`
- Click **Execute**
- If the status is "Running", try again after a few seconds
- Once ready, you’ll get a download link for the CSV report

---

## How It Works (Simple)

- The system converts all store timings into UTC for fair comparison.
- It assumes a store’s status stays the same until the next check (forward-fill method).
- Using this, it calculates uptime and downtime within business