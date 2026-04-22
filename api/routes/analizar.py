import asyncio
import json
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from servicios.ia_service import OrquestadorAgente, validar_anuncio
from api.models.schemas import ResultadoFraude
router = APIRouter(prefix="/analisis", tags=["fraud-detection"])

# El agente se instancia una vez al arrancar la app (singleton)
agente = OrquestadorAgente(pipeline_path="api/models/modelo_hibrido_prueba.pkl")


@router.post("/analizar")
async def analizar_oferta(data: dict):

    try:
        anuncio = await validar_anuncio(data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())


    query = (
        f"Analiza esta oferta de trabajo y determina si es fraudulenta: "
        f"{json.dumps(anuncio, ensure_ascii=False)}"
    )
    loop = asyncio.get_event_loop()
    resultado_raw = await loop.run_in_executor(
        None,
        OrquestadorAgente.ejecutar_tarea,
        query
    )

    try:
        resultado_dict = json.loads(resultado_raw)
        resultado = ResultadoFraude(**resultado_dict)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"El agente no devolvió el formato esperado {exc}")