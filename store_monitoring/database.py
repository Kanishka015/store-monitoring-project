from sqlalchemy import create_engine, Column, Integer, String, DateTime, Time
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///../store.db" 

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class StoreStatus(Base):
    __tablename__ = "store_status"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    timestamp_utc = Column(DateTime, index=True)
    status = Column(String)

class BusinessHours(Base):
    __tablename__ = "business_hours"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    day = Column(Integer)
    start_time_local = Column(Time)
    end_time_local = Column(Time)

class StoreTimezone(Base):
    __tablename__ = "store_timezone"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, unique=True, index=True)
    timezone_str = Column(String, default="America/Chicago")