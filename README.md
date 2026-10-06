# Monitor de Calidad del Aire — Full Stack

Proyecto académico con **frontend web + backend Python/FastAPI conectados**.

## Arquitectura

Navegador → HTML/CSS/JS → FastAPI → OpenAQ API v3 → AQI/OMS → historial CSV.

La clave de OpenAQ se mantiene solo en el servidor.

## Ejecutar localmente

1. Crea una cuenta en OpenAQ y obtén tu API key.
2. Copia `.env.example` como `.env`.
3. Coloca tu clave:

```env
OPENAQ_API_KEY=TU_CLAVE_REAL
ALLOWED_ORIGINS=*
```

4. Crea y activa un entorno virtual.
5. Instala dependencias:

```bash
pip install -r requirements.txt
```

6. Ejecuta:

```bash
uvicorn backend.app:app --reload
```

7. Abre:

```text
http://127.0.0.1:8000
```

La interfaz y la API usan el mismo dominio, por lo que ya quedan conectadas sin modificar `config.js`.

## Endpoints

- `GET /salud`
- `GET /api/ciudad/{ciudad}`
- `GET /api/ciudades`
- `GET /api/historial`
- `GET /api/historial.csv`
- `GET /docs`

## GitHub

Sube todos los archivos de esta carpeta al repositorio. **GitHub almacena el código, pero GitHub Pages no ejecuta Python.**

### Opción recomendada: desplegar todo en Render

El repositorio incluye `render.yaml`.

1. Sube el proyecto a GitHub.
2. En Render crea un Blueprint/Web Service desde el repositorio.
3. Añade la variable secreta `OPENAQ_API_KEY`.
4. Render ejecutará `uvicorn backend.app:app` y servirá tanto la web como la API.

En este modo no necesitas GitHub Pages.

### Si quieres usar GitHub Pages para el frontend

Puedes publicar los archivos estáticos en Pages, pero debes desplegar el backend por separado. Luego cambia en `config.js`:

```js
API_BASE: "https://TU-BACKEND.onrender.com"
```

## Seguridad

No subas `.env` al repositorio. `.gitignore` ya lo excluye.

## Pruebas

```bash
python -m unittest discover tests
```


## Despliegue revisado

La aplicación completa se sirve desde FastAPI: frontend y API comparten dominio.
La presentación anterior permanece en `presentacion/` en GitHub y en el historial Git.
Nunca subir `.env` ni claves reales. Introducir `OPENAQ_API_KEY` solo en Environment de Render.
El blueprint selecciona explícitamente el plan gratuito y comprueba `/salud`.
El estado de salud confirma configuración, no valida la clave contra OpenAQ.

**Historial en Render gratuito:** el CSV es temporal y se pierde al reiniciar o desplegar.
Para conservarlo, hace falta almacenamiento persistente: un disco de Render en un plan
compatible y `DATA_DIR` apuntando al montaje, o una base de datos externa.
No se contrata almacenamiento de pago automáticamente. El CSV usa un único proceso
y bloqueo entre hilos para evitar escrituras simultáneas incompletas.

Las pruebas de integración usan respuestas controladas, no datos reales de OpenAQ.
La verificación en producción necesita una clave válida y estaciones con datos recientes.
