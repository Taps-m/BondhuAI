import requests


def get_weather(city):
    # Find the city's latitude and longitude
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"

    geo_params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    geo_response = requests.get(geo_url, params=geo_params)
    geo_data = geo_response.json()

    if "results" not in geo_data:
        return "Sorry, I couldn't find that city."

    latitude = geo_data["results"][0]["latitude"]
    longitude = geo_data["results"][0]["longitude"]

    # Get current weather
    weather_url = "https://api.open-meteo.com/v1/forecast"

    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "auto"
    }

    weather_response = requests.get(weather_url, params=weather_params)
    weather_data = weather_response.json()

    current = weather_data["current"]

    return (
        f"Temperature: {current['temperature_2m']}°C\n"
        f"Humidity: {current['relative_humidity_2m']}%\n"
        f"Weather code: {current['weather_code']}"
    )