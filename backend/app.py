"""Aplicación FastAPI: API real + frontend del Monitor de Calidad del Aire."""
import csv
import io
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .src.air_quality_service import AirQualityService
from .src.history import FIELDS, read_history
from .src.openaq_client import OpenAQClient, OpenAQError

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

app = FastAPI(
    title="Monitor de Calidad del Aire Colombia",
    version="1.1.0",
    description="Frontend web + backend Python/FastAPI conectado a OpenAQ API v3.",
)

origins_raw = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == ["*"] else origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")


def get_service():
    try:
        return AirQualityService(client=OpenAQClient())
    except OpenAQError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "backend": "Python/FastAPI",
        "openaq_configurada": bool(os.getenv("OPENAQ_API_KEY")),
    }


@app.get("/api/ciudad/{ciudad}")
def calidad_por_ciudad(ciudad: str):
    try:
        return get_service().consultar_ciudad(ciudad, guardar=True)
    except OpenAQError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/ciudades")
def ciudades():
    try:
        return {"ciudades": OpenAQClient().list_cities()}
    except OpenAQError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/historial")
def historial():
    rows = read_history()
    rows.reverse()
    return {"historial": rows}


@app.get("/api/historial.csv")
def descargar_historial():
    rows = read_history()
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        csv.writer(output).writerow(FIELDS)
    data = output.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=historial_calidad_aire.csv"},
    )


@app.get("/")
def frontend():
    return FileResponse(ROOT / "index.html")


@app.get("/{filename:path}")
def frontend_files(filename: str):
    # Solo expone los archivos públicos esperados del frontend.
    allowed = {"styles.css", "script.js", "config.js", ".nojekyll"}
    if filename in allowed:
        return FileResponse(ROOT / filename)
    raise HTTPException(status_code=404, detail="Recurso no encontrado")
