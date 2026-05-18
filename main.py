"""
Módulo de arranque de la aplicación FastAPI.

Define la instancia `app`, monta los recursos estáticos y registra
los routers principales del API. Incluye endpoints de comprobación
de estado (healthcheck) y favicon vacío.
"""

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from api.config import settings
from api.routes import analizar, estadisticas, traduccion

app = FastAPI(
    title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG
)

app.mount(
    "/privacidad", StaticFiles(directory="frontend", html=True), name="privacidad"
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Incluir los routers de las rutas
app.include_router(estadisticas.router, prefix="/api")
app.include_router(analizar.router, prefix="/api")
app.include_router(traduccion.router, prefix="/api")


for route in app.routes:
    print(route.path)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


# Comprobamos que la aplicación se inicia correctamente
@app.get("/")
async def health_check():
    return {"estado": "activo", "app": settings.APP_NAME}


# Ejecución: uvicorn main:app
