import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from enum import Enum
import io


app = FastAPI(
    title="fAIr Job", version="1.0",
    description="API para traducir texto o texto extraído de una imagen."
)
@app.get("/", tags = ["Mensaje Bienvenida"])
async def index():
    return {"Mensaje": "Traducción de un texto/imagen suelto"}

class TargetLanguage(str, Enum):    #Los idiomas que va a tener la interfaz y que devolverá el resultado si el usuario elige uno de estos. Entre comillas su código "ISO"
    english = "en"
    spanish = "es"
    french = "fr"
    german = "de"
    portuguese = "pt"
    italian = "it"
    dutch = "nl"
    russian = "ru"
    arabic = "ar"

async def traducir_contenido(target_lang: str, file: UploadFile = None, text: str = None):  #Creamos esta función para llamarla en el main.py

    if not file and not text:       #Comprobador de posibles errores
        raise HTTPException(status_code=400, detail="Se debe proporcionar un archivo de imagen o texto.")

    extracted_text = ""     #En esta variable se guarda el texto ORIGINAL

    # --- OCR ---  #Código a mejorar, necesitamos las funciones del procesamiento de imagen
    if file:
        if file.content_type not in ["image/jpeg", "image/png", "image/tiff"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado.")

        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        extracted_text = pytesseract.image_to_string(image)

    # --- Texto directo --- #Código a mejorar, necesitamos las funciones del procesamiento de texto
    if text:
        extracted_text = text

    if not extracted_text.strip():
        return "", ""

    # --- Traducción ---
    translator = GoogleTranslator(source='auto', target=target_lang)
    translated = translator.translate(extracted_text)

    return extracted_text, translated

@app.post("/traducir/")     #Sirve para comprobar que la traducción automática es correcta
async def translate_content(target_lang: TargetLanguage = Form(...), file: UploadFile = File(None), text: str = Form(None)):

    original, translated = await traducir_contenido(target_lang.value, file, text)

    return {
        "original_text": original,
        "translated_text": translated,
        "target_language": target_lang.value
    }

#Ejecución (solo este archivo): uvicorn servicios.traduccion_service:app --reload