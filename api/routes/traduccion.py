from fastapi import APIRouter
from pydantic import BaseModel
from api.models.schemas import TextoDetectar, ResultadoDeteccion

router = APIRouter()


#Endpoint para detectar el idioma del texto

@router.post("/detectar_idioma", response_model=ResultadoDeteccion)
async def detectar_idioma(texto: TextoDetectar):
    # Aquí se implementaría la lógica de detección de idioma
    # Por ahora, se devuelve un resultado simulado

    resultado = ResultadoDeteccion(
        idioma_detectado="es",
        es_analizable=True,
        mensaje="El texto es en español y es analizable."
    )
    return resultado