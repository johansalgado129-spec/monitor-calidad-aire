"""Logica principal del monitor de calidad del aire."""

from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean

from .aqi import (
    calculate_pm25_aqi,
    calculate_no2_aqi,
    calculate_o3_aqi,
    aqi_category,
    who_comparison,
    to_ugm3,
    to_ppb,
    to_ppm,
)
from .history import save_record
from .openaq_client import OpenAQClient, OpenAQError


class AirQualityService:
    def __init__(self, client=None, max_sensors_per_pollutant=5):
        self.client = client or OpenAQClient()
        self.max_sensors = max_sensors_per_pollutant

    @staticmethod
    def _recent_values(rows, needed_hours):
        """Toma los valores horarios mas recientes y descarta nulos."""
        valid = [row for row in rows if row.get("value") is not None]

        def sort_key(row):
            period = row.get("period") or {}
            dt_to = period.get("datetimeTo") or {}
            return dt_to.get("utc") or ""

        valid.sort(key=sort_key, reverse=True)
        return valid[:needed_hours]

    @staticmethod
    def _average_in_unit(rows, parameter, target_unit):
        values = []
        for row in rows:
            value = row.get("value")
            units = (row.get("parameter") or {}).get("units")

            if target_unit == "ug/m3":
                converted = to_ugm3(parameter, value, units)
            elif target_unit == "ppb":
                converted = to_ppb(parameter, value, units)
            elif target_unit == "ppm":
                converted = to_ppm(parameter, value, units)
            else:
                converted = None

            if converted is not None:
                values.append(converted)

        return mean(values) if values else None

    def _collect_sensors(self, locations):
        """Agrupa sensores por contaminante y evita duplicados."""
        grouped = defaultdict(list)
        used_ids = set()

        for location in locations:
            for sensor in self.client.target_sensors(location):
                sensor_id = sensor["sensor_id"]
                if not sensor_id or sensor_id in used_ids:
                    continue
                used_ids.add(sensor_id)
                sensor["station_name"] = location.get("name") or "Sin nombre"
                sensor["locality"] = location.get("locality") or ""
                grouped[sensor["parameter"]].append(sensor)

        for parameter in grouped:
            grouped[parameter] = grouped[parameter][: self.max_sensors]

        return grouped

    def _sensor_average(self, sensor, parameter, hours, target_unit):
        rows = self.client.get_sensor_hours(sensor["sensor_id"], hours=hours)
        rows = self._recent_values(rows, hours)
        if not rows:
            return None
        return self._average_in_unit(rows, parameter, target_unit)

    def _city_average(self, sensors, parameter, hours, target_unit):
        station_values = []
        stations = []

        for sensor in sensors:
            try:
                value = self._sensor_average(
                    sensor,
                    parameter=parameter,
                    hours=hours,
                    target_unit=target_unit,
                )
            except OpenAQError:
                continue

            if value is not None:
                station_values.append(value)
                stations.append(sensor["station_name"])

        if not station_values:
            return None, []

        return mean(station_values), stations

    def consultar_ciudad(self, ciudad, guardar=True):
        locations = self.client.find_locations_by_city(ciudad)

        if not locations:
            raise OpenAQError(
                f"No se encontraron estaciones para '{ciudad}' en los datos "
                "actuales de OpenAQ. Prueba con la opcion de listar ciudades."
            )

        sensors = self._collect_sensors(locations)

        # PM2.5: 24 h en ug/m3.
        pm25_24, st_pm = self._city_average(
            sensors.get("pm25", []), "pm25", 24, "ug/m3"
        )

        # NO2: EPA 1 h en ppb y OMS 24 h en ug/m3.
        no2_1, st_no2_1 = self._city_average(
            sensors.get("no2", []), "no2", 1, "ppb"
        )
        no2_24, st_no2_24 = self._city_average(
            sensors.get("no2", []), "no2", 24, "ug/m3"
        )

        # O3: EPA 8 h en ppm. Ademas se conserva equivalente OMS en ug/m3.
        o3_8_ppm, st_o3 = self._city_average(
            sensors.get("o3", []), "o3", 8, "ppm"
        )
        o3_1_ppm, _ = self._city_average(
            sensors.get("o3", []), "o3", 1, "ppm"
        )
        o3_8_ug, _ = self._city_average(
            sensors.get("o3", []), "o3", 8, "ug/m3"
        )

        aqi_pm25 = calculate_pm25_aqi(pm25_24) if pm25_24 is not None else None
        aqi_no2 = calculate_no2_aqi(no2_1) if no2_1 is not None else None
        aqi_o3 = (
            calculate_o3_aqi(o3_8_ppm, o3_1_ppm)
            if o3_8_ppm is not None
            else None
        )

        aqis = {
            "pm25": aqi_pm25,
            "no2": aqi_no2,
            "o3": aqi_o3,
        }
        valid_aqis = {k: v for k, v in aqis.items() if v is not None}

        if not valid_aqis:
            raise OpenAQError(
                "Se encontraron estaciones, pero no hay datos recientes suficientes "
                "de PM2.5, NO2 u O3 para calcular el AQI."
            )

        dominant = max(valid_aqis, key=valid_aqis.get)
        overall_aqi = valid_aqis[dominant]
        category = aqi_category(overall_aqi)

        who = {
            "pm25": who_comparison("pm25", pm25_24),
            "no2": who_comparison("no2", no2_24),
            "o3": who_comparison("o3", o3_8_ug),
        }

        station_names = sorted(set(st_pm + st_no2_1 + st_no2_24 + st_o3))

        result = {
            "fecha": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "ciudad": ciudad.strip().title(),
            "estaciones_encontradas": len(locations),
            "estaciones_utilizadas": station_names,
            "contaminante_dominante": dominant,
            "aqi": overall_aqi,
            "categoria": category["categoria"],
            "nivel": category["nivel"],
            "recomendacion": category["mensaje"],
            "aqi_por_contaminante": aqis,
            "mediciones": {
                "pm25_24h_ug_m3": round(pm25_24, 3) if pm25_24 is not None else None,
                "no2_1h_ppb": round(no2_1, 3) if no2_1 is not None else None,
                "no2_24h_ug_m3": round(no2_24, 3) if no2_24 is not None else None,
                "o3_8h_ppm": round(o3_8_ppm, 6) if o3_8_ppm is not None else None,
                "o3_8h_ug_m3": round(o3_8_ug, 3) if o3_8_ug is not None else None,
            },
            "oms": who,
            "fuente": "OpenAQ API v3",
            "nota": (
                "Resultado informativo. La disponibilidad depende de las estaciones "
                "publicadas por OpenAQ y no reemplaza alertas oficiales."
            ),
        }

        if guardar:
            summary = []
            for parameter, item in who.items():
                if item:
                    summary.append(f"{parameter.upper()}: {item['estado']}")

            save_record(
                {
                    "fecha": result["fecha"],
                    "ciudad": result["ciudad"],
                    "estaciones_utilizadas": " | ".join(station_names),
                    "contaminante_dominante": dominant,
                    "aqi": overall_aqi,
                    "categoria": category["categoria"],
                    "pm25_24h_ug_m3": result["mediciones"]["pm25_24h_ug_m3"],
                    "no2_1h_ppb": result["mediciones"]["no2_1h_ppb"],
                    "no2_24h_ug_m3": result["mediciones"]["no2_24h_ug_m3"],
                    "o3_8h_ppm": result["mediciones"]["o3_8h_ppm"],
                    "o3_8h_ug_m3": result["mediciones"]["o3_8h_ug_m3"],
                    "oms_resumen": " | ".join(summary),
                }
            )

        return result
