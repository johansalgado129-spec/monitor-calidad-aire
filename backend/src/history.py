"""Persistencia CSV del historial del prototipo web."""
import csv
import os
from threading import RLock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = Path(os.getenv("DATA_DIR", str(ROOT / "data"))) / "historial_calidad_aire.csv"
_LOCK = RLock()
FIELDS = [
    "fecha", "ciudad", "estaciones_utilizadas", "contaminante_dominante",
    "aqi", "categoria", "pm25_24h_ug_m3", "no2_1h_ppb",
    "no2_24h_ug_m3", "o3_8h_ppm", "o3_8h_ug_m3", "oms_resumen",
]

def save_record(record):
    with _LOCK:
        _save_record(record)

def _save_record(record):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    exists = HISTORY_PATH.exists()
    with HISTORY_PATH.open("a", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: record.get(field, "") for field in FIELDS})

def read_history():
    with _LOCK:
        return _read_history()

def _read_history():
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open("r", newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))
