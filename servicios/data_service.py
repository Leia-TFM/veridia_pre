import os
import json
from datetime import datetime
from api.config import settings
from collections import Counter



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
        "resultado": resultado,
    }

    with open(settings.DATASET_FILE, "a", encoding="utf-8") as fh:
        json.dump(registro, fh, ensure_ascii=False)
        fh.write("\n")

    return registro

# Cargar registros para análisis
def cargar_registros() -> list[dict]:
    if not os.path.exists(settings.DATASET_FILE):
        return []
    registros = []
    with open(settings.DATASET_FILE, "r", encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if linea:
                try:
                    registros.append(json.loads(linea))
                except json.JSONDecodeError:
                    continue
    return registros

#estadísticas individuales
def estadisticas_anuncios(registros: list[dict]| None = None) -> dict:
    if registros is None: 
        registros = cargar_registros()
    
    conteo = Counter()
    for r in registros:
        veredicto = (r.get("resultado") or {}).get("veredicto", "")
        if veredicto == "FRAUDULENT":
            conteo["fraudulent"] += 1
        elif veredicto == "LEGITIMATE":
            conteo["legitimate"] += 1
        elif veredicto:
            conteo["amarillo"] += 1
        else:
            conteo["sin_veredicto"] += 1

    return {
            "total"       : len(registros),
            "fraudulent"  : conteo["fraudulent"],
            "legitimate"  : conteo["legitimate"],
            "amarillo"    : conteo["amarillo"],
            "sin_veredicto": conteo["sin_veredicto"],
        }

#estadísticas por idioma
def estadisticas_por_idioma(registros: list[dict]| None = None) -> dict:
    if registros is None:
        registros = cargar_registros()

    conteo = Counter()
    for r in registros:
        idioma = r.get("idioma_detectado") or "desconocido"
        conteo[idioma] += 1

    return {
        "idiomas"         : dict(conteo.most_common()),
        "total_con_idioma": sum(conteo.values()),
    }

#estadísticas por tipo de anuncio
def estadisticas_por_tipo(registros: list[dict]| None = None) -> dict:
    if registros is None:
        registros = cargar_registros()

    conteo = Counter()
    for r in registros:
        tipo = r.get("tipo_entrada") or "desconocido"
        if "." in tipo:
            tipo = tipo.split(".")[-1]
        conteo[tipo] += 1

    return {
        "tipos"         : dict(conteo.most_common()),
        "total": sum(conteo.values()),
    }

#estaditicas señales de fraude
def estadisticas_senales(registros: list[dict] | None = None, top_n: int = 10) -> dict:
    if registros is None:
        registros = cargar_registros()
    
    conteo = Counter()
    for r in registros:
        senales = (r.get("resultado") or {}).get("senales") or []
        if isinstance(senales, list):
            for senal in senales:
                if senal and str(senal).strip():
                    conteo[str(senal).strip()] += 1
        elif isinstance(senales, dict):
            # Por si llega en formato dict (versiones anteriores del sistema)
            for key, val in senales.items():
                if isinstance(val, list):
                    for s in val:
                        if s:
                            conteo[str(s).strip()] += 1

    return {
        "senales": dict(conteo.most_common(top_n)),
        "top_n"  : top_n,
    }

def estadisticas_completas() -> dict:
    registros = cargar_registros()
    return {
        "resumen_general": estadisticas_anuncios(registros),
        "por_idioma": estadisticas_por_idioma(registros),
        "por_tipo": estadisticas_por_tipo(registros),
        "senales_frecuentes": estadisticas_senales(registros, top_n=20),
    }