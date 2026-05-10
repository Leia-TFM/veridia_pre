from fastapi import FastAPI
from api.config import settings
from api.routes import analizar, traduccion, estadisticas


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Incluir los routers de las rutas
app.include_router(estadisticas.router, prefix="/api")
app.include_router(analizar.router, prefix="/api")
app.include_router(traduccion.router, prefix="/api")


for route in app.routes:
    print(route.path)
#Comprobamos que la aplicación se inicia correctamente
@app.get("/")
async def health_check():
    return {"estado":"activo", "app":settings.APP_NAME}

#Ejecución: uvicorn main:app
