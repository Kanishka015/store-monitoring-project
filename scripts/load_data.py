import pandas as pd
from sqlalchemy.orm import Session
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from store_monitoring.database import engine, SessionLocal, Base, StoreStatus, BusinessHours, StoreTimezone

def setup_database_schema():
    Base.metadata.create_all(bind=engine)

def load_csv_data():
    try:
        print("Loading store status data... (this may take a moment)")
        df_status = pd.read_csv('data/store_status.csv')
        df_status['timestamp_utc'] = pd.to_datetime(df_status['timestamp_utc'].str.replace(' UTC', ''))
        df_status.to_sql('store_status', con=engine, if_exists='append', index=False)
        print("Store status data loaded.")

        print("\nLoading business hours data...")
        df_hours = pd.read_csv('data/menu_hours.csv')
        df_hours.rename(columns={'dayOfWeek': 'day'}, inplace=True)
        df_hours.to_sql('business_hours', con=engine, if_exists='append', index=False)
        print("Business hours data loaded.")
        
        print("\nLoading timezone data...")
        df_tz = pd.read_csv('data/timezones.csv')
        df_tz.to_sql('store_timezone', con=engine, if_exists='append', index=False)
        print("Timezone data loaded.")

        print("\nAll data has been successfully loaded into the database.")

    except Exception as e:
        print(f"An error occurred during data loading: {e}")


if __name__ == "__main__":
    print("--- Starting Database Setup and Data Loading ---")
    setup_database_schema()
    load_csv_data()
    print("--- Process Complete ---")
