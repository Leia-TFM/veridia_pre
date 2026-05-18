"""
Servicio de persistencia y estadísticas locales.

Provee utilidades para guardar registros de análisis en un fichero
JSONL y funciones de agregación/estadística para consumo por el API.
"""

import json
import os
from collections import Counter
from datetime import datetime

from api.config import settings


def guardar_datos(
    anuncio: dict,
    original_text: str,
    translated_text: str,
    idioma_detectado: str,
    resultado: dict,
) -> dict:
    """
    Guarda un registro de análisis de anuncio para entrenamiento o fine-tuning posterior.

    El registro se escribe en un archivo JSON Lines local para preservar el texto original,
    la traducción, el idioma detectado y la respuesta del agente.
    """
    os.makedirs(settings.DATASET_DIR, exist_ok=True)

    registro = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tipo_entrada": (
            str(anuncio.get("tipo")) if anuncio.get("tipo") is not None else None
        ),
        "idioma_destino": (
            str(anuncio.get("idioma_destino"))
            if anuncio.get("idioma_destino") is not None
            else None
        ),
        "idioma_detectado": idioma_detectado,
        "url": anuncio.get("url"),
        # Normalizar la clave de veredicto internamente a `verdict` para evitar
        # inconsistencias entre 'veredicto'/'verdicto'/'verdict'.
        "resultado": _normalize_resultado(resultado),
    }

    with open(settings.DATASET_FILE, "a", encoding="utf-8") as fh:
        json.dump(registro, fh, ensure_ascii=False)
        fh.write("\n")

    return registro


# Cargar registros para análisis
def cargar_registros() -> list[dict]:
    """
    Carga todos los registros almacenados en el fichero JSONL.

    Cada línea del fichero es un objeto JSON independiente. Si el fichero no
    existe devuelve una lista vacía.
    """
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


# estadísticas individuales
def estadisticas_anuncios(registros: list[dict] | None = None) -> dict:
    """
    Calcula un resumen simple de veredictos a partir de los registros.

    Soporta claves legacy (`veredicto`, `verdicto`) y la nueva `verdict`.
    """
    if registros is None:
        registros = cargar_registros()

    conteo = Counter()
    for r in registros:
        resultado = r.get("resultado") or {}
        # Soportar claves legacy y la nueva 'verdict'
        veredicto = (
            resultado.get("verdict")
            or resultado.get("veredicto")
            or resultado.get("verdicto")
            or ""
        )
        if veredicto == "FRAUDULENT":
            conteo["fraudulent"] += 1
        elif veredicto == "LEGITIMATE":
            conteo["legitimate"] += 1
        elif veredicto:
            conteo["amarillo"] += 1
        else:
            conteo["sin_veredicto"] += 1

    return {
        "total": len(registros),
        "fraudulent": conteo["fraudulent"],
        "legitimate": conteo["legitimate"],
        "amarillo": conteo["amarillo"],
        "sin_veredicto": conteo["sin_veredicto"],
    }


# estadísticas por idioma
def estadisticas_por_idioma(registros: list[dict] | None = None) -> dict:
    """
    Devuelve la distribución de registros por idioma detectado.
    """
    if registros is None:
        registros = cargar_registros()

    conteo = Counter()
    for r in registros:
        idioma = r.get("idioma_detectado") or "desconocido"
        conteo[idioma] += 1

    return {
        "idiomas": dict(conteo.most_common()),
        "total_con_idioma": sum(conteo.values()),
    }


# estadísticas por tipo de anuncio
def estadisticas_por_tipo(registros: list[dict] | None = None) -> dict:
    """
    Devuelve la distribución de registros por tipo de entrada (texto/url/imagen).
    """
    if registros is None:
        registros = cargar_registros()

    conteo = Counter()
    for r in registros:
        tipo = r.get("tipo_entrada") or "desconocido"
        if "." in tipo:
            tipo = tipo.split(".")[-1]
        conteo[tipo] += 1

    return {
        "tipos": dict(conteo.most_common()),
        "total": sum(conteo.values()),
    }


# estaditicas señales de fraude
def estadisticas_senales(registros: list[dict] | None = None, top_n: int = 10) -> dict:
    """
    Extrae y cuenta las señales detectadas en los resultados almacenados.

    Devuelve un diccionario con las `top_n` señales más frecuentes.
    """
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
        "top_n": top_n,
    }


def _normalize_resultado(resultado: dict) -> dict:
    """
    Normaliza la estructura del resultado para almacenamiento.

    - Asegura que la clave principal de veredicto sea `verdict` (valor en mayúsculas).
    - No altera otras claves útiles.
    """
    if not isinstance(resultado, dict):
        return resultado

    out = dict(resultado)

    # Casos legacy: 'veredicto' (es) o 'verdicto' (typo) → unificar a 'verdict'
    legacy = out.pop("veredicto", None)
    legacy2 = out.pop("verdicto", None)

    current = out.get("verdict")
    if not current and legacy:
        out["verdict"] = legacy
    elif not current and legacy2:
        out["verdict"] = legacy2

    # Normalizar valor a mayúsculas si existe
    if isinstance(out.get("verdict"), str):
        out["verdict"] = out["verdict"].upper()

    return out


def estadisticas_completas() -> dict:
    """Compone un resumen completo con varias estadísticas agregadas."""
    registros = cargar_registros()
    return {
        "resumen_general": estadisticas_anuncios(registros),
        "por_idioma": estadisticas_por_idioma(registros),
        "por_tipo": estadisticas_por_tipo(registros),
        "senales_frecuentes": estadisticas_senales(registros, top_n=20),
    }
