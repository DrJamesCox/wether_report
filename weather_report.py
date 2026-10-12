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

class Current_Weather(BaseModel):
    temperature: float
    windspeed: float
    winddirection: int
    time: str
    interval: int
    is_day: int
    weathercode: str

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


if __name__ == "__main__":
    main()
