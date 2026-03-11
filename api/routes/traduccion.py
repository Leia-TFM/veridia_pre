from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, List
import pytesseract
from PIL import Image
import os

import sys
# --- Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición) ---
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

import requests
import sqlite3
from collections import Counter
from deep_translator import GoogleTranslator #Traduccion automática
from servicios.traduccion_service import traducir_contenido, TargetLanguage    #Archivo desde donde se hace la traducción automática



app = FastAPI(title="fAIr Job", version="1.0")   #Inicialización de la API

@app.get("/", tags = ["Mensaje Bienvenida"])     
async def index():
    return {"Mensaje": "¡Bienvenidos a fAIr Job!"}  #Mensaje por defecto cuando ejecutas 

class ResultadoAnalisis (BaseModel):        #Modelo base, lo que queremos mostrar por pantalla tras pegar el anuncio, esto irá en schemas.py
    semaforo: str
    puntuacion: int
    mensaje_usuario: str
    motivos: List[str]

class EstadisticasONG (BaseModel):          #Modelo base, si es usuario quiere comprabar las estadísticas de otros anuncios, esto irá en schemas.py
    total_analisis: int
    fraudes_detectados: int
    patrones_comunes: List[str]
    tasa_fraude: float

@app.post("/api/traducir", response_model=ResultadoAnalisis)
async def traducir_anuncio(
    texto: Optional[str] = Form(None),                             #Variable opcional por si el anuncio es texto
    url: Optional[str] = Form(None),                               #Variable opcional por si el anuncio es una url
    foto: Optional[UploadFile] = File(None),                       #Variable opcional por si el anuncio es una imagen (con OCR)
    idioma: TargetLanguage = Form(TargetLanguage.spanish)          #Desde el idioma base (español) traduce a los demás idiomas recogidos en el archivo "traduccion_service.py"
):

    texto_original, texto_traducido = await traducir_contenido(idioma.value, foto, texto)       #Línea que traduce el texto/imagen desde la función de traduccion_service.py

    contenido = texto_traducido.lower() if texto_traducido else ""

    #Necesitamos las funciones/código del grupo de procesamiento de texto y sobretodo el procesamiento de imagen 

    riesgo = "VERDE"            #PRUEBA, lo que se verá por pantalla en la web
    score = 10
    motivos = []

    mensaje = GoogleTranslator(source='es', target=idioma.value).translate(     #Este es el mensaje que devuelve por pantalla en la interfaz según el idioma del usuario, con el ejemplo
        "¡Cuidado! Este anuncio tiene indicios de trata."
    )

    return {        #Lo que devuelve de momento el archivo
        "semaforo": riesgo,
        "puntuacion": score,
        "mensaje_usuario": mensaje,
        "motivos": motivos
    }

print("\nConectando con la API...")

#PASO 1: COMANDO CON EL REQUIREMENTS
#requirements:  pip install -r requirements.txt

# Ejecución: uvicorn api.routes.traduccion:app --reload + en otra terminal el streamlit de app.py
# Ejecución (local): uvicorn traduccion:app --reload + en otra terminal el streamlit de app.py