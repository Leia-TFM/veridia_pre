import os
import json
from datetime import datetime
from api.config import settings



def guardar_datos(anuncio: dict, original_text: str, translated_text: str, idioma_detectado: str, resultado: dict) -> dict:
    """
    Guarda un registro de análisis de anuncio para entrenamiento o fine-tuning posterior.

    El registro se escribe en un archivo JSON Lines local para preservar el texto original,
    la traducción, el idioma detectado y la respuesta del agente.
    """
    os.makedirs(settings.DATASET_DIR, exist_ok=True)

    registro = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tipo_entrada": str(anuncio.get("tipo")) if anuncio.get("tipo") is not None else None,
        "idioma_destino": str(anuncio.get("idioma_destino")) if anuncio.get("idioma_destino") is not None else None,
        "idioma_detectado": idioma_detectado,
        "url": anuncio.get("url"),
        "texto_entrada": anuncio.get("texto"),
        "texto_original": original_text,
        "texto_traducido": translated_text,
        "resultado": resultado,
    }

    with open(settings.DATASET_FILE, "a", encoding="utf-8") as fh:
        json.dump(registro, fh, ensure_ascii=False)
        fh.write("\n")

    return registro


#Funcion para sacar los rasgos mas usados
#def estadisticas_rasgos_mas_usados:

#Funcion para sacar la cantidad de fraudes detectados
#def estadisticas_fraudes:

#Funcion para sacar el numero de anuncios analizados
#def estadisticas_anuncios:

#Funcion general para los gráficos
#def generar_estadisticas_gráficos: