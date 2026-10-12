# inspect_weather.py
from pathlib import Path
from textwrap import indent

import requests
import json


def run_weather_fetch() -> None:
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


    print(f"Request URL: {response.url}")
    print(f"Status Code: {response.status_code}")

    output_file = Path("weather_report.json")
    output_file.write_text(response.text, encoding="utf-8")
    print(f"Saved response to {output_file.name}. Open it and find the temperature!")



if __name__ == "__main__":
    run_weather_fetch()