import os
import sys

from fastapi import APIRouter

root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

from api.models.schemas import DistribucionSemaforo, EstadisticasGenerales
from servicios.data_service import estadisticas_completas

router = APIRouter()


@router.get("/estadisticas", response_model=EstadisticasGenerales)
async def obtener_estadisticas():
    """Recupera las estadísticas agregadas de los anuncios almacenados."""

    stats = estadisticas_completas()
    resumen = stats["resumen_general"]
    por_idioma = stats["por_idioma"]
    senales = stats["senales_frecuentes"]

    return EstadisticasGenerales(
        total_analizados=resumen["total"],
        distribucion_semaforo=DistribucionSemaforo(
            verde=resumen["legitimate"],
            amarillo=resumen["amarillo"],
            rojo=resumen["fraudulent"],
        ),
        indicadores_frecuentes=senales["senales"],
        idiomas_frecuentes=por_idioma["idiomas"],
    )
