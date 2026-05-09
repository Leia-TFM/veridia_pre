
from fastapi import APIRouter
import os
import sys
# --- Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición) ---
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)
from api.models.schemas import DistribucionSemaforo, EstadisticasGenerales

router = APIRouter()

# --- ENDPOINT ---
@router.get("/estadisticas", response_model=EstadisticasGenerales)
async def obtener_estadisticas():
    # Aquí se implementaría la lógica para calcular las estadísticas reales
    return EstadisticasGenerales(
        total_analizados=100,
        distribucion_semaforo=DistribucionSemaforo(
            verde=60,
            amarillo=25,
            rojo=15
        ),
        indicadores_frecuentes={
            "trabajo inmediato": 34,
            "sin experiencia": 28,
            "alojamiento incluido": 21
        },
        idiomas_frecuentes={
            "es": 75,
            "en": 20,
            "fr": 5
        }
    )
