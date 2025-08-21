# store_monitoring/main.py

import uuid
import pandas as pd
import os
import pytz
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

# Import database session and our core calculation logic.
from .database import SessionLocal
from .logic import calculate_store_uptime

app = FastAPI()

# In-memory storage for report status.
reports = {}

def generate_report_logic(report_id: str):
    """The background task that generates the full report."""
    db = SessionLocal()
    try:
        # Get all unique store IDs.
        store_ids_query = text("SELECT DISTINCT store_id FROM store_status")
        store_ids = [result[0] for result in db.execute(store_ids_query).fetchall()]
        
        # Determine the report's "current time" from the latest data point.
        max_timestamp_query = text("SELECT MAX(timestamp_utc) FROM store_status")
        max_timestamp_str = db.execute(max_timestamp_query).scalar()
        
        if max_timestamp_str:
            try:
                current_utc_time = datetime.strptime(max_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                current_utc_time = datetime.strptime(max_timestamp_str, '%Y-%m-%d %H:%M:%S')
        else:
            current_utc_time = datetime.utcnow() # Fallback if no data.
        
        current_utc_time = current_utc_time.replace(tzinfo=pytz.UTC)

        # Calculate uptime/downtime for each store.
        report_data = []
        # Limiting to first 10 stores for faster report generation during testing
        for store_id in store_ids[:10]: 
            store_report = calculate_store_uptime(db, store_id, current_utc_time)
            report_data.append(store_report)
        
        # Save the report to a CSV file.
        df = pd.DataFrame(report_data)
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True) # Ensure the 'reports' directory exists.
        file_path = os.path.join(reports_dir, f"{report_id}.csv")
        df.to_csv(file_path, index=False)
        
        # Mark the report as complete.
        reports[report_id].update({"status": "Complete", "file_path": file_path})

    except Exception as e:
        reports[report_id]["status"] = "Error"
        print(f"Error generating report {report_id}: {e}")
    finally:
        db.close()


@app.post("/trigger_report")
def trigger_report(background_tasks: BackgroundTasks):
    """API endpoint to trigger a new report generation."""
    report_id = str(uuid.uuid4())
    reports[report_id] = {"status": "Running"}
    
    # Run the main logic as a background task.
    background_tasks.add_task(generate_report_logic, report_id)
    
    return {"report_id": report_id}


@app.get("/get_report")
def get_report(report_id: str):
    """API endpoint to get the status or the final report CSV."""
    report_info = reports.get(report_id)
    
    if not report_info:
        return JSONResponse(status_code=404, content={"error": "Report not found"})
        
    if report_info["status"] == "Running":
        return {"status": "Running"}
        
    if report_info["status"] == "Complete":
        return FileResponse(path=report_info["file_path"], media_type='text/csv', filename=f"{report_id}.csv")

    return JSONResponse(status_code=500, content={"error": "Report generation failed"})
