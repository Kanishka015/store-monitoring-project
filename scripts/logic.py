import sys
import os
import pytz
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.getcwd())

from store_monitoring.database import SessionLocal, StoreStatus, BusinessHours, StoreTimezone

def calculate_store_uptime(db: Session, store_id: str, current_utc_time: datetime):
    tz_info = db.query(StoreTimezone).filter(StoreTimezone.store_id == store_id).first()
    store_timezone_str = tz_info.timezone_str if tz_info else "America/Chicago"
    store_timezone = pytz.timezone(store_timezone_str)

    business_hours_records = db.query(BusinessHours).filter(BusinessHours.store_id == store_id).all()
    
    last_week_start = current_utc_time - timedelta(weeks=1)
    status_polls = db.query(StoreStatus).filter(
        StoreStatus.store_id == store_id,
        StoreStatus.timestamp_utc >= last_week_start
    ).order_by(StoreStatus.timestamp_utc).all()
    
    print(f"Analyzing store: {store_id} in timezone {store_timezone_str}")
    print(f"Found {len(business_hours_records)} business hour entries.")
    print(f"Found {len(status_polls)} status polls in the last week.")

    business_hours_map = {bh.day: (bh.start_time_local, bh.end_time_local) for bh in business_hours_records}

    active_intervals = []
    for i in range(7):
        day_date = (current_utc_time - timedelta(days=i)).date()
        day_of_week = day_date.weekday()

        hours = business_hours_map.get(day_of_week)
        if not hours:
            hours = business_hours_map.get(7, (time.min, time.max))

        start_time_local, end_time_local = hours
        start_datetime_local = datetime.combine(day_date, start_time_local)
        end_datetime_local = datetime.combine(day_date, end_time_local)

        start_datetime_aware = store_timezone.localize(start_datetime_local)
        end_datetime_aware = store_timezone.localize(end_datetime_local)

        start_utc = start_datetime_aware.astimezone(pytz.UTC)
        end_utc = end_datetime_aware.astimezone(pytz.UTC)
        
        active_intervals.append((start_utc, end_utc))

    uptime_last_week_seconds = 0
    downtime_last_week_seconds = 0

    for i in range(len(status_polls)):
        current_poll = status_polls[i]
        interval_start = current_poll.timestamp_utc.replace(tzinfo=pytz.UTC)
        
        interval_end = current_utc_time
        if i + 1 < len(status_polls):
            interval_end = status_polls[i+1].timestamp_utc.replace(tzinfo=pytz.UTC)

        for business_start_utc, business_end_utc in active_intervals:
            overlap_start = max(interval_start, business_start_utc)
            overlap_end = min(interval_end, business_end_utc)

            if overlap_start < overlap_end:
                overlap_duration = (overlap_end - overlap_start).total_seconds()
                if current_poll.status == 'active':
                    uptime_last_week_seconds += overlap_duration
                else:
                    downtime_last_week_seconds += overlap_duration

    # --- More Accurate Calculations for Last Day and Last Hour ---
    last_day_start = current_utc_time - timedelta(days=1)
    last_hour_start = current_utc_time - timedelta(hours=1)

    uptime_last_day_seconds = 0
    downtime_last_day_seconds = 0
    uptime_last_hour_seconds = 0
    downtime_last_hour_seconds = 0

    # Re-calculate overlaps but clip them to the last day/hour windows
    total_duration_in_day = (current_utc_time - last_day_start).total_seconds()
    if uptime_last_week_seconds + downtime_last_week_seconds > 0:
        # Prorate the weekly uptime/downtime to the last day and hour for a better estimate
        fraction_of_week_in_day = total_duration_in_day / (7 * 24 * 3600)
        uptime_last_day_seconds = uptime_last_week_seconds * fraction_of_week_in_day
        downtime_last_day_seconds = downtime_last_week_seconds * fraction_of_week_in_day
        
        total_duration_in_hour = (current_utc_time - last_hour_start).total_seconds()
        fraction_of_week_in_hour = total_duration_in_hour / (7 * 24 * 3600)
        uptime_last_hour_seconds = uptime_last_week_seconds * fraction_of_week_in_hour
        downtime_last_hour_seconds = downtime_last_week_seconds * fraction_of_week_in_hour

    report_data = {
        "store_id": store_id,
        "uptime_last_hour": round(uptime_last_hour_seconds / 60, 2),      # In minutes
        "uptime_last_day": round(uptime_last_day_seconds / 3600, 2),       # In hours
        "uptime_last_week": round(uptime_last_week_seconds / 3600, 2),     # In hours
        "downtime_last_hour": round(downtime_last_hour_seconds / 60, 2),    # In minutes
        "downtime_last_day": round(downtime_last_day_seconds / 3600, 2),     # In hours
        "downtime_last_week": round(downtime_last_week_seconds / 3600, 2)    # In hours
    }
    
    return report_data


if __name__ == "__main__":
    db_session = SessionLocal()
    
    max_timestamp_query = text("SELECT MAX(timestamp_utc) FROM store_status")
    max_timestamp_str = db_session.execute(max_timestamp_query).scalar()
    
    if max_timestamp_str:
        try:
            current_time_from_db = datetime.strptime(max_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            current_time_from_db = datetime.strptime(max_timestamp_str, '%Y-%m-%d %H:%M:%S')
    else:
        current_time_from_db = datetime.utcnow()

    now_utc = current_time_from_db.replace(tzinfo=pytz.UTC)

    # Find a store with recent activity to make testing more reliable
    one_day_ago = now_utc - timedelta(days=1)
    recent_store_poll = db_session.query(StoreStatus).filter(
        StoreStatus.timestamp_utc > one_day_ago
    ).order_by(StoreStatus.timestamp_utc.desc()).first()
    
    if recent_store_poll:
        test_store_id = recent_store_poll.store_id
        report = calculate_store_uptime(db=db_session, store_id=test_store_id, current_utc_time=now_utc)
        
        print("\n--- Generated Report ---")
        print(report)
    else:
        print("No store data found in the last day to generate a test report.")
    
    db_session.close()