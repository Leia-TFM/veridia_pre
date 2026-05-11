from deep_translator import GoogleTranslator
from fastapi import UploadFile, HTTPException
import logging   
import fasttext
import os
from difflib import SequenceMatcher
from servicios.texto_service import process_image_input, process_text_input, process_url_input

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lid.176.ftz")   #Modelo de detección del idioma

model = fasttext.load_model(MODEL_PATH)

# La librería logging registra eventos durante la ejecución: errores, advertencias e información de flujo.
# A diferencia de print(), permite clasificar los mensajes por nivel de gravedad:
#   - logger.info()    → confirmación de que algo ha funcionado correctamente
#   - logger.warning() → algo inesperado, pero el programa sigue funcionando
#   - logger.error()   → error grave que ha impedido ejecutar una operación
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tamaño máximo de imagen permitido en MB.
# Si no se pone un límite, una imagen muy grande puede saturar la memoria del servidor.
MAX_IMAGE_SIZE_MB = 10

# Formatos de imagen que acepta la API.
# Se amplían respecto al original (solo jpeg, png, tiff) para cubrir más casos de uso.
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/tiff", "image/webp", "image/bmp"}


async def traducir_contenido(target_lang: str, file: UploadFile = None, text: str = None, url: str = None):
    #Función principal que extrae y traduce el contenido. Se llama desde traduccion.py.

    # Comprobador de errores: se debe proporcionar al menos un tipo de contenido
    if not file and not text and not url:
        raise HTTPException(status_code=400, detail="Se debe proporcionar imagen, texto o URL.")

    # Comprobador de errores: no se permiten imagen y texto a la vez, es ambiguo
    if sum(x is not None for x in [file, text, url]) > 1:
        raise HTTPException(status_code=400, detail="Proporciona solo una entrada: imagen, texto o URL.")
    
    # Variable que acumula el texto a traducir (imagen + texto directo)
    texto_para_traducir = ""

    # --- OCR ---
    if file:
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(status_code=415, detail="Formato de archivo no soportado.")

        image_bytes = await file.read()

        if len(image_bytes) / (1024 * 1024) > MAX_IMAGE_SIZE_MB:
            raise HTTPException(status_code=413, detail=f"La imagen supera el tamaño máximo de {MAX_IMAGE_SIZE_MB} MB.")

        resultado = process_image_input(image_bytes)

        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get("mensaje", "No se pudo extraer texto de la imagen.")
            )

        
        logger.info("Texto extraído de imagen correctamente.")

    # --- Texto directo ---
    if text:
        resultado = process_text_input(text)
        
        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get("mensaje", "Texto no válido.")
            )

        
    # -------- URL --------
    if url:
        resultado = process_url_input(url)

        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get("mensaje", "No se pudo procesar la URL.")
            )
    
    # Comprobador de errores: ¿el texto resultante tiene contenido legible?
    if not texto_para_traducir.strip():
        return {
            "original": "",
            "traducido": "",
            "idioma_detectado": "Unknown",
            "confianza_idioma": 0.0,
            "confianza_traduccion": 0.0
        }

    # Comprobación de longitud mínima para detectar idioma
    if len(texto_para_traducir.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="El texto es demasiado corto para detectar el idioma."
        )
    # --- Comprobador de idioma ---
    # El texto de entrada debe estar en español, inglés o francés (objetivos mínimos del proyecto).
    # Si se detecta otro idioma, el mensaje de error se muestra en el idioma del usuario
    # para que pueda entenderlo aunque no sepa español.
    # Si la detección falla (sin conexión, texto muy corto...) se deja pasar para no bloquear la petición.
    try:
        texto_limpio = " ".join(texto_para_traducir.split())
        pred = model.predict(texto_limpio)

        etiqueta = pred[0][0]
        probabilidad = pred[1][0]

        idioma_detectado = etiqueta.replace("__label__", "")

        logger.info(f"Idioma detectado: {idioma_detectado} (confianza: {probabilidad})")

        # Umbral de confianza
        if probabilidad < 0.5:
            idioma_detectado = "Unknown"
            logger.warning("Confianza baja en la detección de idioma.")

    except Exception as e:
        logger.warning(f"No se pudo detectar el idioma de entrada: {e}")
        idioma_detectado = "Unknown"
        probabilidad = 0.0

    # --- Traducción ---
    try:
        source_lang = idioma_detectado if idioma_detectado != "Unknown" else "auto"
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        # Se limita a 4500 caracteres para evitar bloqueos del servicio de traducción de Google
        translated = translator.translate(texto_para_traducir[:4500])

        # --- Traducción inversa (Comprobadoir de que la traducción es fiable)---
        back_translator = GoogleTranslator(
            source=target_lang,
            target=source_lang
        )

        retranslated = back_translator.translate(translated)

        # --- Métrica de similitud (mismas métricas que la detección de idioma, no muestra fiabilidad con OCR pero traduce bien)---
        score = SequenceMatcher(
            None,
            texto_para_traducir.lower(),
            retranslated.lower()
        ).ratio()

        logger.info(
            f"Confianza traducción: {round(score, 3)}"
        )

        return texto_para_traducir, translated, idioma_detectado
    
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        # 502 Bad Gateway: el fallo es del servicio externo (Google Translate), no de nuestra API
        raise HTTPException(status_code=502, detail="El servicio de traducción no está disponible. Inténtalo más tarde.")


#PASO 1: COMANDO CON EL REQUIREMENTS
#requirements:  pip install -r requirements.txt

#Ejecución (solo este archivo): uvicorn servicios.traduccion_service:app --reload
#Ejecución local (solo este archivo): uvicorn traduccion_service:app --reload