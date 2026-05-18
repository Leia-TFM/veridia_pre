"""Rutas para detección de idioma y traducción de contenido."""

import os
import sys

from fastapi import APIRouter, Depends, File, UploadFile

# "Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición)"
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

from api.models.schemas import ResultadoDeteccion, TextoDetectar
from servicios.traduccion_service import traducir_contenido

router = APIRouter()


@router.post("/detectar_idioma", response_model=ResultadoDeteccion)
async def detectar_idioma(
    texto: TextoDetectar = Depends(TextoDetectar.as_form), file: UploadFile = File(None)
):

    # "Extrae contenido y detecta idioma usando la función de traduccion_service.py"
    """Detecta el idioma de la entrada y devuelve la traducción si procede."""

    original, translated, idioma_detectado = await traducir_contenido(
        target_lang=texto.idioma_destino, file=file, text=texto.texto, url=texto.url
    )

    # Verificar que el idioma detectado es español para devolver el resultado de la detección/traducción
    if idioma_detectado != "es":
        return ResultadoDeteccion(
            idioma_detectado=idioma_detectado,
            es_analizable=False,
            mensaje="",
            original=original,
            traducido="",
        )

    resultado = ResultadoDeteccion(
        idioma_detectado=idioma_detectado,
        es_analizable=True,
        mensaje="",
        original=original,
        traducido=translated,
    )

    return resultado
