# inspect_weather.py
from pathlib import Path
from pydantic import BaseModel, ValidationError
import datetime
from sqlmodel import Field, SQLModel, create_engine, Session, select
import requests
import json

# =================================================
# 1. Request weather and store JSON
# =================================================


# =================================================
# 2. Validation Models
# =================================================

class Current_Weather_Units(BaseModel):
    time: str
    interval: str
    temperature: str
    windspeed: str
    winddirection: str
    is_day: str
    weathercode: str

class Current_Weather(BaseModel):
    temperature: float
    windspeed: float
    winddirection: int
    time: str
    interval: int
    is_day: int
    weathercode: int

class Weather(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    current_weather_units: Current_Weather_Units
    current_weather: Current_Weather


# =================================================
# 3. Database table (SQLModel) - only what we want to store
# =================================================
# WHY A SEPARATE CLASS? In a SQLModel table (table=True), EVERY field becomes
# a column. Field(sa_column=None) does NOT exclude a field, because None is
# already the default. The clean way to store only some fields is to keep the
# API shape (CurrentWeather above) separate from the table shape (below).


class WeatherRecord(SQLModel, table=True):
    __tablename__ = "weather_history"

    # Add a database primary key id that isn't required in the API payload
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    # The 3 specific fields requested (Validated and stored)
    temperature: float  # celsius
    windspeed: float    # km/h
    winddirection: int  # degrees


# ==========================================================
# 4. Database Configuration
# ==========================================================
DATABASE_URL = "sqlite:///./weather_sqlmodel_2.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """Builds the SQLite table layout out-of-the-box"""
    SQLModel.metadata.create_all(engine)

# =================================================
# 5. Pipeline Steps
# =================================================

# 5.1 Fetch Weather
def run_weather_fetch() -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 29.4241,
        "longitude": -98.4936,
        "current_weather": "true",
    }

    print("Requesting live weather data...")
    response = requests.get(url, params=params)

    print(f"response:\n{response.text}")
    response_text = response.text
    response_dict = json.loads(response_text)

    print(type(response_dict))
    print("RESPONSE\n=================\n",response_dict,"\n=============================")


    print(f"Request URL: {response.url}")
    print(f"Status Code: {response.status_code}")

    output_file = Path("weather_report.json")
    output_file.write_text(response.text, encoding="utf-8")
    print(f"Saved response to {output_file.name}. Open it and find the temperature!")
    return response_dict


# 5.2 Validate Weather: Validate JSON shape and data types
def validate_weather(response_dict: dict) -> Weather | None:
    try:
        weather_report = Weather.model_validate(response_dict)
        print("YAY!!!!")
        print(weather_report)
        print(type(weather_report)) # <class '__main__.Weather'
        return weather_report

    except ValidationError as e:
        print("Validation failed:", e.json())
        return None

# 5.3 Save weather_report to DB
def save_weather_report(weather_report: Weather) -> None:
    """Copy the fields we care about into a table row and commit it."""
    current = weather_report.current_weather
    record = WeatherRecord(
        temperature=current.temperature,
        windspeed=current.windspeed,
        winddirection=current.winddirection,
    )

    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        print(f"Record saved to DB: {record}")

# 5.4 Print the DB contents
def print_db():
    with Session(engine) as session:
        records = session.exec(select(WeatherRecord)).all()
        for record in records:
            print(record)

# =================================================
# 5. Entry point
# =================================================

def main():
    print("MAIN")
    init_db()
    raw_weather = run_weather_fetch()
    report = validate_weather(raw_weather)
    if report is not None:
        save_weather_report(report)
        # print_db()



if __name__ == "__main__":
    main()
    print_db()
