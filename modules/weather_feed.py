import json
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime, date

from PyQt6.QtCore import QObject, pyqtSignal

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search?name={}&count=1&language=pt&format=json"
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
    "&hourly=temperature_2m,weather_code"
    "&daily=weather_code,temperature_2m_max,temperature_2m_min"
    "&timezone=auto&forecast_days=5"
)

WMO_CODES = {
    0:  ("Céu limpo",            "☀"),
    1:  ("Predominante limpo",   "🌤"),
    2:  ("Parcialmente nublado", "⛅"),
    3:  ("Nublado",              "☁"),
    45: ("Neblina",              "🌫"),
    48: ("Neblina c/ geada",     "🌫"),
    51: ("Garoa leve",           "🌦"),
    53: ("Garoa moderada",       "🌦"),
    55: ("Garoa densa",          "🌦"),
    61: ("Chuva leve",           "🌧"),
    63: ("Chuva moderada",       "🌧"),
    65: ("Chuva forte",          "🌧"),
    71: ("Neve leve",            "🌨"),
    73: ("Neve moderada",        "🌨"),
    75: ("Neve forte",           "🌨"),
    77: ("Granizo",              "🌨"),
    80: ("Pancadas leves",       "🌦"),
    81: ("Pancadas moderadas",   "🌦"),
    82: ("Pancadas fortes",      "🌧"),
    85: ("Neve fraca",           "🌨"),
    86: ("Neve forte",           "🌨"),
    95: ("Trovoada",             "⛈"),
    96: ("Trovoada c/ granizo",  "⛈"),
    99: ("Trovoada intensa",     "⛈"),
}

_DAYS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


class WeatherFeedModule(QObject):
    weather_updated = pyqtSignal(dict)
    error           = pyqtSignal(str)

    def __init__(self, interval: int = 600):
        super().__init__()
        self.interval   = interval
        self._city      = ""
        self._lat       = None
        self._lon       = None
        self._city_name = ""
        self._country   = ""
        self._running   = False

    def set_city(self, city: str):
        self._city      = city.strip()
        self._lat       = None
        self._lon       = None
        self._city_name = ""
        self._country   = ""
        self.refresh()

    def start(self):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()

    def refresh(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _run(self):
        while self._running:
            self._fetch()
            time.sleep(self.interval)

    def _fetch(self):
        if not self._city:
            return
        try:
            if self._lat is None:
                url = GEOCODE_URL.format(urllib.parse.quote(self._city))
                with urllib.request.urlopen(url, timeout=8) as r:
                    geo = json.loads(r.read())
                results = geo.get("results")
                if not results:
                    self.error.emit(f"Cidade '{self._city}' não encontrada")
                    return
                self._lat       = results[0]["latitude"]
                self._lon       = results[0]["longitude"]
                self._city_name = results[0].get("name", self._city)
                self._country   = results[0].get("country_code", "").upper()

            url = WEATHER_URL.format(lat=self._lat, lon=self._lon)
            with urllib.request.urlopen(url, timeout=8) as r:
                data = json.loads(r.read())

            cur    = data["current"]
            hourly = data["hourly"]
            daily  = data["daily"]

            code        = cur["weather_code"]
            desc, emoji = WMO_CODES.get(code, ("--", "🌡"))

            now_dt      = datetime.fromisoformat(cur["time"])
            hourly_list = []
            for i, t in enumerate(hourly["time"]):
                dt = datetime.fromisoformat(t)
                if dt > now_dt and len(hourly_list) < 8:
                    _, em = WMO_CODES.get(hourly["weather_code"][i], ("", "🌡"))
                    hourly_list.append({
                        "hour":  dt.strftime("%Hh"),
                        "temp":  round(hourly["temperature_2m"][i]),
                        "emoji": em,
                    })

            today      = date.today()
            daily_list = []
            for i, d in enumerate(daily["time"]):
                day_dt = date.fromisoformat(d)
                if day_dt < today:
                    continue
                _, em = WMO_CODES.get(daily["weather_code"][i], ("", "🌡"))
                label = "Hoje" if day_dt == today else _DAYS_PT[day_dt.weekday()]
                daily_list.append({
                    "day":   label,
                    "emoji": em,
                    "max":   round(daily["temperature_2m_max"][i]),
                    "min":   round(daily["temperature_2m_min"][i]),
                })
                if len(daily_list) >= 5:
                    break

            self.weather_updated.emit({
                "city":       self._city_name,
                "country":    self._country,
                "temp":       round(cur["temperature_2m"]),
                "feels_like": round(cur["apparent_temperature"]),
                "humidity":   cur["relative_humidity_2m"],
                "wind":       round(cur["wind_speed_10m"]),
                "desc":       desc,
                "emoji":      emoji,
                "hourly":     hourly_list,
                "daily":      daily_list,
            })

        except Exception as e:
            self.error.emit(str(e)[:80])
