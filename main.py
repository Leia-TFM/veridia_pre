from fastapi import FastAPI
import os
import sys
# --- Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición) ---
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

from config import settings    #from api.config import settings
from routes import analizar, traduccion #from api.routes import analizar, traduccion, estadisticas 

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Incluir los routers de las rutas
app.include_router(analizar.router, prefix="/api")
app.include_router(traduccion.router, prefix="/api")
#app.include_router(estadisticas.router, prefix="/api")

#Comprobamos que la aplicación se inicia correctamente
@app.get("/")
async def health_check():
    return {"estado":"activo", "app":settings.APP_NAME}

#Ejecución (local): uvicorn main:app --reload
#Ejecución : uvicorn api.main:app --reload