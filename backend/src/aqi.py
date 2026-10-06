"""Funciones para calcular AQI EPA y comparar con guias OMS."""

from math import floor

# AQI EPA 2024+ para PM2.5 (24 h), en ug/m3.
PM25_BREAKPOINTS = [
    (0.0, 9.0, 0, 50),
    (9.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 125.4, 151, 200),
    (125.5, 225.4, 201, 300),
    (225.5, 325.4, 301, 500),
]

# NO2 EPA (1 h), en ppb.
NO2_BREAKPOINTS = [
    (0.0, 53.0, 0, 50),
    (54.0, 100.0, 51, 100),
    (101.0, 360.0, 101, 150),
    (361.0, 649.0, 151, 200),
    (650.0, 1249.0, 201, 300),
    (1250.0, 2049.0, 301, 500),
]

# O3 EPA (8 h), en ppm. El AQI de 8 h llega hasta la categoria 201-300.
O3_8H_BREAKPOINTS = [
    (0.000, 0.054, 0, 50),
    (0.055, 0.070, 51, 100),
    (0.071, 0.085, 101, 150),
    (0.086, 0.105, 151, 200),
    (0.106, 0.200, 201, 300),
]

# O3 EPA (1 h), utilizado para concentraciones altas.
O3_1H_BREAKPOINTS = [
    (0.125, 0.164, 101, 150),
    (0.165, 0.204, 151, 200),
    (0.205, 0.404, 201, 300),
    (0.405, 0.604, 301, 500),
]

# Guias OMS 2021 de corto plazo.
WHO_SHORT_TERM_UGM3 = {
    "pm25": 15.0,  # 24 h
    "no2": 25.0,   # 24 h
    "o3": 100.0,   # maximo diario de media 8 h
}

MOLECULAR_WEIGHT = {
    "no2": 46.0055,
    "o3": 48.0,
}


def _interpolate(concentration, c_low, c_high, i_low, i_high):
    """Formula lineal del AQI."""
    if c_high == c_low:
        return i_high
    value = ((i_high - i_low) / (c_high - c_low)) * (
        concentration - c_low
    ) + i_low
    return round(value)


def _find_aqi(concentration, breakpoints):
    """Busca el intervalo correspondiente y calcula el AQI."""
    if concentration < 0:
        return None

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            return _interpolate(concentration, c_low, c_high, i_low, i_high)

    # Por encima de la tabla se limita a 500 para la presentacion del proyecto.
    if concentration > breakpoints[-1][1]:
        return 500
    return None


def calculate_pm25_aqi(value_ugm3):
    """AQI para PM2.5. EPA usa concentracion de 24 horas."""
    concentration = floor(float(value_ugm3) * 10) / 10
    return _find_aqi(concentration, PM25_BREAKPOINTS)


def calculate_no2_aqi(value_ppb):
    """AQI para NO2 usando concentracion de 1 hora."""
    concentration = floor(float(value_ppb))
    return _find_aqi(concentration, NO2_BREAKPOINTS)


def calculate_o3_aqi(value_8h_ppm, value_1h_ppm=None):
    """AQI para ozono.

    Para concentraciones de 8 h hasta 0.200 ppm se usa la tabla de 8 h.
    Si supera ese nivel y existe dato de 1 h, se usa la tabla de 1 h.
    """
    c8 = floor(float(value_8h_ppm) * 1000) / 1000

    if c8 <= 0.200:
        return _find_aqi(c8, O3_8H_BREAKPOINTS)

    if value_1h_ppm is not None:
        c1 = floor(float(value_1h_ppm) * 1000) / 1000
        return _find_aqi(c1, O3_1H_BREAKPOINTS)

    return 300


def aqi_category(aqi):
    """Devuelve categoria, nivel y recomendacion general."""
    if aqi is None:
        return {
            "categoria": "Sin datos",
            "nivel": "desconocido",
            "mensaje": "No hay datos suficientes para clasificar.",
        }
    if aqi <= 50:
        return {
            "categoria": "Buena",
            "nivel": "bajo",
            "mensaje": "La calidad del aire se considera satisfactoria.",
        }
    if aqi <= 100:
        return {
            "categoria": "Moderada",
            "nivel": "moderado",
            "mensaje": "Personas muy sensibles pueden tomar precauciones.",
        }
    if aqi <= 150:
        return {
            "categoria": "Insalubre para grupos sensibles",
            "nivel": "alto para sensibles",
            "mensaje": "Grupos sensibles deben reducir esfuerzos prolongados al aire libre.",
        }
    if aqi <= 200:
        return {
            "categoria": "Insalubre",
            "nivel": "alto",
            "mensaje": "Se recomienda reducir actividades intensas al aire libre.",
        }
    if aqi <= 300:
        return {
            "categoria": "Muy insalubre",
            "nivel": "muy alto",
            "mensaje": "Conviene limitar la exposicion al aire libre.",
        }
    return {
        "categoria": "Peligrosa",
        "nivel": "peligroso",
        "mensaje": "Evite exposicion innecesaria al aire libre y consulte alertas oficiales.",
    }


def who_comparison(parameter, value_ugm3):
    """Compara el promedio con la guia OMS de corto plazo."""
    limit = WHO_SHORT_TERM_UGM3.get(parameter)
    if limit is None or value_ugm3 is None:
        return None

    exceeds = float(value_ugm3) > limit
    return {
        "limite_ug_m3": limit,
        "valor_ug_m3": round(float(value_ugm3), 3),
        "supera_guia": exceeds,
        "estado": "Supera guia OMS" if exceeds else "Dentro de guia OMS",
    }


def normalize_unit(unit):
    """Normaliza distintas formas de escribir unidades."""
    text = (unit or "").strip().lower()
    replacements = {
        "µ": "u",
        "μ": "u",
        "³": "3",
        "^3": "3",
        " ": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def to_ugm3(parameter, value, unit):
    """Convierte una concentracion a ug/m3 cuando es posible.

    Conversion de gases aproximada a 25 C y 1 atm.
    """
    if value is None:
        return None

    value = float(value)
    u = normalize_unit(unit)

    if u in {"ug/m3", "ugm-3", "ugm3"}:
        return value
    if u in {"mg/m3", "mgm-3", "mgm3"}:
        return value * 1000.0

    if parameter not in MOLECULAR_WEIGHT:
        return None

    mw = MOLECULAR_WEIGHT[parameter]

    if u == "ppb":
        return value * mw / 24.45
    if u == "ppm":
        return value * 1000.0 * mw / 24.45

    return None


def to_ppb(parameter, value, unit):
    """Convierte NO2 a ppb cuando es posible."""
    if value is None:
        return None
    value = float(value)
    u = normalize_unit(unit)

    if u == "ppb":
        return value
    if u == "ppm":
        return value * 1000.0

    ugm3 = to_ugm3(parameter, value, unit)
    if ugm3 is None or parameter not in MOLECULAR_WEIGHT:
        return None
    return ugm3 * 24.45 / MOLECULAR_WEIGHT[parameter]


def to_ppm(parameter, value, unit):
    """Convierte O3 a ppm cuando es posible."""
    if value is None:
        return None
    value = float(value)
    u = normalize_unit(unit)

    if u == "ppm":
        return value
    if u == "ppb":
        return value / 1000.0

    ugm3 = to_ugm3(parameter, value, unit)
    if ugm3 is None or parameter not in MOLECULAR_WEIGHT:
        return None
    return ugm3 * 24.45 / (MOLECULAR_WEIGHT[parameter] * 1000.0)
