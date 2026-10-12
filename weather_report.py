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

# =================================================
# 2. Validate JSON
# =================================================

class Current_Weather_Units(BaseModel):
    time: str
    interval: str
    temperature: str
    windspeed: str
    winddirection: str
    is_day: str
    weathercode: str

class Current_Weather(SQLModel, table=True):
    __tablename__ = "weather_history"

    # Add a database primary key id that isn't required in the API payload
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    # The 3 specific fields requested (Validated and stored)
    temperature: float
    windspeed: float
    winddirection: int

    # Fields present in payload but ignored by database columns (sa_column=None)
    time: str = Field(sa_column=None)
    interval: int = Field(sa_column=None)
    is_day: int = Field(sa_column=None)
    weathercode: int = Field(sa_column=None)

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


# ==========================================================
# Database Configuration
# ==========================================================
DATABASE_URL = "sqlite:///./weather_sqlmodel.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """Builds the SQLite table layout out-of-the-box"""
    SQLModel.metadata.create_all(engine)

# =================================================
# This is what runs the process
# =================================================

def main():
    print("MAIN")
    weather = run_weather_fetch()
    try:
        weather_report = Weather.model_validate(weather)
        print("YAY!!!!")
        print(weather_report)
        print(type(weather_report)) # <class '__main__.Weather'

    except ValidationError as e:
        print("Validation failed:", e.json())

    # Save directly to the local SQLite file
    init_db()
    try:
        db_record = weather_report.current_weather
        with Session(engine) as session:
            session.add(db_record)
            session.commit()
            print(f"💾 Saved to SQLite via SQLModel -> Temp: {db_record.temperature}, Wind: {db_record.windspeed}")
    except Exception as e:
        print(f"❌ Pipeline processing failed: {e}")
        print("=" * 20, "\n", weather_report.current_weather, "\n", "+" * 20)
        print(type(weather_report.current_weather)) #<class '__main__.Current_Weather'


def print_db():
    with Session(engine) as session:
        records = session.exec(select(Current_Weather)).all()
        for record in records:
            print(record)
if __name__ == "__main__":
    main()
    print_db()
