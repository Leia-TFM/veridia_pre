import asyncio
import json
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from servicios.ia_service import OrquestadorAgente, validar_anuncio

router = APIRouter(prefix="/analisis", tags=["fraud-detection"])

# El agente se instancia una vez al arrancar la app (singleton)
agente = OrquestadorAgente(pipeline_path="models/fraud_pipeline.pkl")


@router.post("/analizar")
async def analizar_oferta(data: dict):

    # ── Capa 1 y 2: Pydantic + regex + Qwen ──────────────────────────────
    try:
        validacion = await validar_anuncio(data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al contactar con el modelo semántico: {exc.response.status_code}"
        )

    # ── Capa 3: agente ML ─────────────────────────────────────────────────
    # ejecutar_tarea es síncrono → lo movemos a un thread para no bloquear
    # el event loop de FastAPI
    query = (
        f"Analiza esta oferta de trabajo y determina si es fraudulenta: "
        f"{json.dumps(validacion['anuncio'], ensure_ascii=False)}"
    )
    loop = asyncio.get_event_loop()
    resultado_ml = await loop.run_in_executor(
        None,
        OrquestadorAgente.ejecutar_tarea,
        query
    )

    return {
        "alertas_ia"      : validacion["alertas_ia"],
        "nivel_riesgo_ia" : validacion["nivel_riesgo_ia"],
        "justificacion_ia": validacion["justificacion_ia"],
        "resultado_ml"    : resultado_ml,
    }