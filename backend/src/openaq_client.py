"""Cliente sencillo para OpenAQ API v3."""

import os
import unicodedata
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openaq.org/v3"
TARGET_PARAMETERS = {"pm25", "no2", "o3"}


class OpenAQError(Exception):
    pass


def normalize_text(text):
    """Quita tildes y normaliza para comparar nombres de ciudades."""
    text = (text or "").strip().lower()
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


class OpenAQClient:
    def __init__(self, api_key=None, timeout=25):
        self.api_key = api_key or os.getenv("OPENAQ_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            raise OpenAQError(
                "No se encontro OPENAQ_API_KEY. Copia .env.example como .env "
                "y agrega tu API key de OpenAQ."
            )

        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

    def _get(self, path, params=None):
        url = f"{BASE_URL}{path}"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise OpenAQError(f"No fue posible conectarse con OpenAQ: {exc}") from exc

        if response.status_code == 401:
            raise OpenAQError("La API key de OpenAQ no es valida o no fue aceptada.")
        if response.status_code == 429:
            raise OpenAQError("Se alcanzo temporalmente el limite de consultas de OpenAQ.")
        if not response.ok:
            raise OpenAQError(
                f"OpenAQ respondio con HTTP {response.status_code}."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise OpenAQError("OpenAQ devolvio una respuesta no valida.") from exc

    def get_colombia_locations(self, max_pages=10):
        """Descarga las estaciones/localizaciones publicadas para Colombia."""
        locations = []
        page = 1
        limit = 100

        while page <= max_pages:
            data = self._get(
                "/locations",
                params={
                    "iso": "CO",
                    "limit": limit,
                    "page": page,
                    "mobile": "false",
                },
            )

            results = data.get("results", [])
            locations.extend(results)

            if len(results) < limit:
                break

            found = data.get("meta", {}).get("found")
            if isinstance(found, int) and len(locations) >= found:
                break

            page += 1

        return locations

    def list_cities(self):
        """Retorna localidades unicas reportadas por OpenAQ en Colombia."""
        values = set()
        for location in self.get_colombia_locations():
            locality = location.get("locality")
            if locality:
                values.add(locality.strip())
        return sorted(values, key=normalize_text)

    def find_locations_by_city(self, city):
        """Busca estaciones por localidad o por nombre de estacion."""
        query = normalize_text(city)
        if not query:
            return []

        locations = self.get_colombia_locations()
        exact = []
        partial = []

        for item in locations:
            locality = normalize_text(item.get("locality"))
            name = normalize_text(item.get("name"))

            if query == locality:
                exact.append(item)
            elif query in locality or query in name:
                partial.append(item)

        return exact if exact else partial

    def get_sensor_hours(self, sensor_id, hours=24):
        """Obtiene valores horarios recientes de un sensor."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=hours + 2)

        data = self._get(
            f"/sensors/{sensor_id}/hours",
            params={
                "datetime_from": start.isoformat(),
                "datetime_to": now.isoformat(),
                "limit": min(100, hours + 10),
                "page": 1,
            },
        )
        return data.get("results", [])

    @staticmethod
    def target_sensors(location):
        """Extrae sensores PM2.5, NO2 y O3 de una estacion."""
        result = []
        for sensor in location.get("sensors", []):
            parameter = sensor.get("parameter", {})
            name = (parameter.get("name") or "").lower()
            if name in TARGET_PARAMETERS:
                result.append(
                    {
                        "sensor_id": sensor.get("id"),
                        "sensor_name": sensor.get("name"),
                        "parameter": name,
                        "unit": parameter.get("units"),
                    }
                )
        return result
