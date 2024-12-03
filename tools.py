import requests, json

with open("credentials.yml", "r") as c:
    lines = c.readlines()
    weather_key = lines[1].strip()

def weather():
    city = "Dortmund"
    days = 1

    url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_key}&q={city}&days={days}&aqi=no&alerts=no"

    response = requests.get(url)
    data = response.json()

    temperature = data['current']['temp_c']
    rain_amount = data['current']['precip_mm']
    sun_hours = data['current']['uv']
    rain_probability = data['forecast']['forecastday'][0]['day']['daily_chance_of_rain']
    windspeed = data['current']['wind_kph']
    humidity = data['current']['humidity']
    pressure = data['current']['pressure_mb']
    uv_index = data['current']['uv']

    return (temperature, rain_probability)
    return {"temp": temperature, "rain_amount": rain_amount, "sun_hrs": sun_hours, "pop": rain_probability, "wind": windspeed, "hum": humidity, "pressure": pressure, "uv": uv_index}