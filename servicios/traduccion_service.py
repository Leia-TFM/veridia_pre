# "El archivo traduccion_service.py se encarga de la detección y traducción
# de un texto para traducir (en formato string, url o imagen) en español"

# "Librerías y funciones encargadas de la traducción, procesamiento y detección de texto"
from deep_translator import GoogleTranslator
from fastapi import UploadFile, HTTPException
import logging   
import fasttext
import os
from difflib import SequenceMatcher
from servicios.texto_service import process_image_input, process_text_input, process_url_input

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# "Modelo de detección del idioma"
MODEL_PATH = os.path.join(BASE_DIR, "lid.176.ftz")   

# "Importación del modelo de detección (Fasttext)"
model = fasttext.load_model(MODEL_PATH)

# "La librería logging registra eventos durante la ejecución: errores, advertencias e información de flujo.
# A diferencia de print(), permite clasificar los mensajes por nivel de gravedad:
#   - logger.info()    → confirmación de que algo ha funcionado correctamente
#   - logger.warning() → algo inesperado, pero el programa sigue funcionando
#   - logger.error()   → error grave que ha impedido ejecutar una operación"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# "Tamaño máximo de imagen permitido en MB. Una imagen muy grande puede saturar la memoria del servidor."
MAX_IMAGE_SIZE_MB = 10

# "Formatos de imagen que acepta la API.""
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/tiff", "image/webp", "image/bmp"}

# "Función principal asíncrona que detecta, extrae y traduce el contenido. Se llama desde traduccion.py."
# "Recibe de argumentos un idioma destino (el traducido), un string para el texto bruto, un string para la url
# y una imagen con el formato UploadFile de FastAPI"
async def traducir_contenido(target_lang: str, file: UploadFile = None, text: str = None, url: str = None):

    # "Comprobador de errores: se debe proporcionar al menos un tipo de contenido"
    if not file and not text and not url:
        raise HTTPException(status_code=400, detail="Se debe proporcionar imagen, texto o URL.")

    # "Comprobador de errores: no se permiten imagen y texto a la vez, es ambiguo"
    if sum(x is not None for x in [file, text, url]) > 1:
        raise HTTPException(status_code=400, detail="Proporciona solo una entrada: imagen, texto o URL.")
    
    # "Variable que acumula el texto a traducir (imagen + texto directo (texto bruto o url))"
    texto_para_traducir = ""

    # "Caso de anuncio que es una imagen con comprobadores de errores y procesamiento del texto para la traducción"
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

    # "Caso de anuncio que es texto bruto con comprobadores de errores y procesamiento del texto para la traducción"
    if text:
        resultado = process_text_input(text)
        
        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get("mensaje", "Texto no válido.")
            )

        
    # "Caso de anuncio que es una url con comprobadores de errores y procesamiento del texto para la traducción"
    if url:
        resultado = process_url_input(url)

        texto_para_traducir = resultado["texto_original"]
        if not texto_para_traducir.strip():
            raise HTTPException(
                status_code=422,
                detail=resultado["metadatos"].get("mensaje", "No se pudo procesar la URL.")
            )
    
    # "Comprobador de errores: ¿el texto resultante tiene contenido legible?"
    if not texto_para_traducir.strip():
        return {
            "original": "",
            "traducido": "",
            "idioma_detectado": "Unknown",
            "confianza_idioma": 0.0,
            "confianza_traduccion": 0.0
        }

    # "Comprobación de longitud mínima para detectar idioma"
    if len(texto_para_traducir.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="El texto es demasiado corto para detectar el idioma."
        )
    
    # "Detección de idioma del texto procesado con métricas de confianza
    # El texto de entrada debe estar en español.
    # Si se detecta otro idioma, el mensaje de error se muestra en el idioma del usuario para que pueda entenderlo aunque no sepa español.
    # Si la detección falla (sin conexión, texto muy corto...) se deja pasar para no bloquear la petición (uso de try/except)."
    try:
        texto_limpio = " ".join(texto_para_traducir.split())
        pred = model.predict(texto_limpio)

        etiqueta = pred[0][0]
        probabilidad = pred[1][0]

        idioma_detectado = etiqueta.replace("__label__", "")

        logger.info(f"Idioma detectado: {idioma_detectado} (confianza: {probabilidad})")

        # "Métricas de confianza"
        if probabilidad < 0.5:
            idioma_detectado = "Unknown"
            logger.warning("Confianza baja en la detección de idioma.")

    # "Comprobador de errores: fallo en la detección del idioma del texto procesado"
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
        back_translator = GoogleTranslator(
            source=target_lang,
            target=source_lang
        )

        retranslated = back_translator.translate(translated)

        # "Métrica de similitud (mismas métricas que la detección de idioma)"
        score = SequenceMatcher(
            None,
            texto_para_traducir.lower(),
            retranslated.lower()
        ).ratio()

        logger.info(
            f"Confianza traducción: {round(score, 3)}"
        )

        return texto_para_traducir, translated, idioma_detectado
    
     # "Comprobador de errores: 502 Bad Gateway; el fallo es del servicio externo (Google Translate), no de nuestra API"
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        raise HTTPException(status_code=502, detail="El servicio de traducción no está disponible. Inténtalo más tarde.")
