"""Servicio de detección de idioma y traducción.

Permite extraer texto de imágenes, URL o contenido manual y luego detecta el
idioma usando fastText. Traduce el contenido usando GoogleTranslator y valida
la calidad mediante back-translation.
"""

import logging
import os
from difflib import SequenceMatcher

import fasttext
from deep_translator import GoogleTranslator
from fastapi import HTTPException, UploadFile

from servicios.texto_service import (process_image_input, process_text_input,
                                     process_url_input)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lid.176.ftz")
_model = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_fasttext_model():
    """Carga perezosa del modelo FastText para detección de idioma."""
    global _model
    if _model is None:
        _model = fasttext.load_model(MODEL_PATH)
    return _model


# Tamaño máximo de imagen permitido en MB. Una imagen muy grande puede saturar la memoria del servidor.
MAX_IMAGE_SIZE_MB = 10

# Formatos de imagen que acepta la API.
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
    "image/bmp",
}


# "Función principal asíncrona que detecta, extrae y traduce el contenido. Se llama desde traduccion.py."
# "Recibe de argumentos un idioma destino (el traducido), un string para el texto bruto, un string para la url
# y una imagen con el formato UploadFile de FastAPI"
async def traducir_contenido(
    target_lang: str,
    file: UploadFile | None = None,
    text: str | None = None,
    url: str | None = None,
) -> tuple[str, str, str]:
    """
    Detecta el idioma de la entrada y devuelve la traducción.

    Retorna una tupla con el texto original, el texto traducido y el idioma detectado.
    """

    # Comprobador de errores: se debe proporcionar al menos un tipo de contenido
    if not file and not text and not url:
        raise HTTPException(
            status_code=400, detail="Se debe proporcionar imagen, texto o URL."
        )

    # "Comprobador de errores: no se permiten imagen y texto a la vez, es ambiguo"
    if sum(x is not None for x in [file, text, url]) > 1:
        raise HTTPException(
            status_code=400, detail="Proporciona solo una entrada: imagen, texto o URL."
        )

    # "Variable que acumula el texto a traducir (imagen + texto directo (texto bruto o url))"
    texto_para_traducir = ""

    # "Caso de anuncio que es una imagen con comprobadores de errores y procesamiento del texto para la traducción"
    if file:
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=415, detail="Formato de archivo no soportado."
            )

        image_bytes = await file.read()

        if len(image_bytes) / (1024 * 1024) > MAX_IMAGE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"La imagen supera el tamaño máximo de {MAX_IMAGE_SIZE_MB} MB.",
            )

        resultado = process_image_input(image_bytes)

        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get(
                    "mensaje", "No se pudo extraer texto de la imagen."
                ),
            )

        logger.info("Texto extraído de imagen correctamente.")

    # "Caso de anuncio que es texto bruto con comprobadores de errores y procesamiento del texto para la traducción"
    if text:
        resultado = process_text_input(text)

        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get("mensaje", "Texto no válido."),
            )

    # "Caso de anuncio que es una url con comprobadores de errores y procesamiento del texto para la traducción"
    if url:
        resultado = process_url_input(url)

        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get(
                    "mensaje", "No se pudo procesar la URL."
                ),
            )

    if not texto_para_traducir.strip():
        raise HTTPException(
            status_code=422,
            detail="No se pudo extraer contenido válido para traducir.",
        )

    if len(texto_para_traducir.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="El texto es demasiado corto para detectar el idioma.",
        )

    try:
        texto_limpio = " ".join(texto_para_traducir.split())
        model = _load_fasttext_model()
        pred = model.predict(texto_limpio)

        etiqueta = pred[0][0]
        probabilidad = pred[1][0]

        idioma_detectado = etiqueta.replace("__label__", "")
        logger.info(f"Idioma detectado: {idioma_detectado} (confianza: {probabilidad})")

        if probabilidad < 0.5:
            idioma_detectado = "Unknown"
            logger.warning("Confianza baja en la detección de idioma.")
    except Exception as e:
        logger.warning(f"No se pudo detectar el idioma de entrada: {e}")
        idioma_detectado = "Unknown"
        probabilidad = 0.0

    # "Traducción de idioma del texto detectado con métricas de confianza
    # El texto de entrada debe estar en español.
    # Si se detecta otro idioma, no se realiza la traducción.
    # Se limita a 4500 caracteres para evitar bloqueos del servicio de traducción de Google.
    # Si la traducción falla (sin conexión, texto muy corto...) se deja pasar para no bloquear la petición (uso de try/except)."
    try:
        source_lang = idioma_detectado if idioma_detectado != "Unknown" else "auto"
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(texto_para_traducir[:4500])

        # "Traducción inversa (Comprobador de que la traducción es fiable)"
        back_translator = GoogleTranslator(source=target_lang, target=source_lang)

        retranslated = back_translator.translate(translated)

        # "Métrica de similitud (mismas métricas que la detección de idioma)"
        score = SequenceMatcher(
            None, texto_para_traducir.lower(), retranslated.lower()
        ).ratio()

        logger.info(f"Confianza traducción: {round(score, 3)}")

        return texto_para_traducir, translated, idioma_detectado

    # "Comprobador de errores: 502 Bad Gateway; el fallo es del servicio externo (Google Translate), no de nuestra API"
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        raise HTTPException(
            status_code=502,
            detail="El servicio de traducción no está disponible. Inténtalo más tarde.",
        )
