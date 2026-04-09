import json
import urllib.request
import urllib.parse


def _fetch_json(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def get_weather(location="Mumbai"):
    """Return weather details for a location using wttr.in."""
    query = urllib.parse.quote(location)
    url = f"https://wttr.in/{query}?format=j1"
    data = _fetch_json(url)

    current = data.get("current_condition", [{}])[0]
    area = data.get("nearest_area", [{}])[0]
    weather = {
        "location": area.get("areaName", [{}])[0].get("value", location),
        "region": area.get("region", [{}])[0].get("value", ""),
        "country": area.get("country", [{}])[0].get("value", ""),
        "temperature_c": current.get("temp_C"),
        "temperature_f": current.get("temp_F"),
        "feels_like_c": current.get("FeelsLikeC"),
        "feels_like_f": current.get("FeelsLikeF"),
        "condition": current.get("weatherDesc", [{}])[0].get("value", ""),
        "humidity": current.get("humidity"),
        "wind_kph": current.get("windspeedKmph"),
        "visibility_km": current.get("visibility"),
        "precipitation_mm": current.get("precipMM"),
    }
    return weather


def get_weather_summary(location="New York"):
    weather = get_weather(location)
    return (
        f"Weather for {weather['location']}, {weather['region']}, {weather['country']}: "
        f"{weather['condition']} with {weather['temperature_c']}°C (feels like {weather['feels_like_c']}°C). "
        f"Humidity {weather['humidity']}%, wind {weather['wind_kph']} km/h."
    )
