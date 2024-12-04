import requests, json, time
from datetime import datetime, timedelta

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

def get_timers() -> list:
    with open("saves/timers.json", "r") as j:
        jsonobj = json.load(j)
    return jsonobj["timers"]

def add_timer(tid: str, dur: int) -> None:
    timers = get_timers()
    dt = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    curr_timer = {"timer_id": tid, "duration": dur, "start": dt}
    timers.append(curr_timer)
    f = {"timers": timers}
    with open("saves/timers.json", "w") as t:
        json.dump(f, t)

def check_timers():
    completed = []
    i_compl = []
    timers = get_timers()

    for index, timer in enumerate(timers):
        now_plus_dur = datetime.strptime(timer["start"], "%m/%d/%Y, %H:%M:%S") + timedelta(seconds=timer["duration"])
        if datetime.now() >= now_plus_dur:
            completed.append(timer)
            i_compl.append(index)

    i_compl.reverse()
    for index in i_compl:
        timers.pop(index)

    f = {"timers": timers}
    with open("saves/timers.json", "w") as t:
        json.dump(f, t)

    return completed