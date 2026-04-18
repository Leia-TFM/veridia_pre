import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
from fastapi import UploadFile, HTTPException
import io
import logging   
import requests
from bs4 import BeautifulSoup
import fasttext
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "lid.176.ftz")

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

# -------- EXTRACCIÓN DE TEXTO DE URL --------
def extraer_texto_url(url: str):

    try:
        response = requests.get(url, timeout=10)    #La librería requests nos ayuda a leer el contenido de una url
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # eliminar scripts y estilos
        for script in soup(["script", "style", "noscript"]):
            script.extract()

        texto = soup.get_text(separator=" ")

        # limpiar espacios
        texto = " ".join(texto.split())

        logger.info("Texto extraído de la URL correctamente.")

        return texto[:4500]

    except Exception as e:
        logger.error(f"Error obteniendo texto de URL: {e}")
        raise HTTPException(status_code=400, detail="No se pudo acceder o procesar la URL.")


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
        # Comprobador de errores: formato de imagen no soportado.
        # Se usa 415 Unsupported Media Type en lugar de 400, que es el código HTTP correcto para este caso.
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(status_code=415, detail="Formato de archivo no soportado.")

        image_bytes = await file.read()

        # Comprobador de errores: imagen demasiado grande
        if len(image_bytes) / (1024 * 1024) > MAX_IMAGE_SIZE_MB:
            raise HTTPException(status_code=413, detail=f"La imagen supera el tamaño máximo de {MAX_IMAGE_SIZE_MB} MB.")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # TODO: Reemplazar por la función de procesamiento de imagen del equipo
            # Ejemplo esperado: texto_imagen = procesar_imagen(image)
            texto_imagen = pytesseract.image_to_string(image)   # línea temporal hasta recibir la función del equipo de imagen
            texto_para_traducir += texto_imagen
            logger.info("Texto extraído de imagen correctamente.")
        
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            raise HTTPException(status_code=500, detail="Error interno en el módulo de imagen.")

    # --- Texto directo ---
    if text:
        # TODO: Reemplazar por la función de procesamiento/limpieza de texto del equipo
        # Ejemplo esperado: texto_limpio = procesar_texto(text)
        texto_limpio = text     # línea temporal hasta recibir la función del equipo de texto
        # Se concatena al texto de la imagen (si lo hay) eliminando espacios sobrantes
        texto_para_traducir = f"{texto_para_traducir} {texto_limpio}".strip()
     
    # -------- URL --------
    if url:
        texto_url = extraer_texto_url(url)
        texto_para_traducir = texto_url
    
    # Comprobador de errores: ¿el texto resultante tiene contenido legible?
    if not texto_para_traducir.strip():
        return "", "No se detectó contenido legible para traducir."

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
        pred = model.predict(texto_para_traducir)

        etiqueta = pred[0][0]
        probabilidad = pred[1][0]

        idioma_detectado = etiqueta.replace("__label__", "")

        logger.info(f"Idioma detectado: {idioma_detectado} (confianza: {probabilidad})")

        # Umbral de confianza
        if probabilidad < 0.5:
            idioma_detectado = "unknown"
            logger.warning("Confianza baja en la detección de idioma.")

    except Exception as e:
        logger.warning(f"No se pudo detectar el idioma de entrada: {e}")
        idioma_detectado = "unknown"

    # --- Traducción ---
    try:
        translator = GoogleTranslator(source="es", target=target_lang)
        # Se limita a 4500 caracteres para evitar bloqueos del servicio de traducción de Google
        translated = translator.translate(texto_para_traducir[:4500])
        return texto_para_traducir, translated, idioma_detectado
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        # 502 Bad Gateway: el fallo es del servicio externo (Google Translate), no de nuestra API
        raise HTTPException(status_code=502, detail="El servicio de traducción no está disponible. Inténtalo más tarde.")


#PASO 1: COMANDO CON EL REQUIREMENTS
#requirements:  pip install -r requirements.txt

#Ejecución (solo este archivo): uvicorn servicios.traduccion_service:app --reload
#Ejecución local (solo este archivo): uvicorn traduccion_service:app --reload