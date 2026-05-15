import json
import re
import requests
import spacy
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field, HttpUrl
from trafilatura import extract, fetch_url
from trafilatura.settings import use_config
from servicios.ocr_service import extraer_texto


nlp = spacy.load("es_core_news_sm")
NLP_MODEL_NAME = "es_core_news_sm"

stopwords_basicas = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "o", "u", "pero", "sino", "aunque", "como"
}


def clean_text(text: str) -> dict:
    """
    Limpia y normaliza el texto.
    """
    if not text or not isinstance(text, str):
        return {
            "tokens": [],
            "texto_limpio": "",
            "texto_normalizado": ""
        }

    texto = re.sub(r'\bref\s*:?\s*\d+\b', '', text, flags=re.IGNORECASE)
    texto = re.sub(r'([a-zA-Záéíóúñ])(\d)', r'\1 \2', texto)
    texto = re.sub(r'(\d)([a-zA-Záéíóúñ])', r'\1 \2', texto)
    texto = re.sub(r'[^\w\s@\.\:\/\+\-\€\$%\!,\(\)#\n]', ' ', texto)
    texto = texto.lower()
    texto = re.sub(r'\s+', ' ', texto).strip()

    doc = nlp(texto)

    tokens = []
    for token in doc:
        if token.is_space:
            continue

        if token.is_punct and token.text not in ['!', '?', ',', '.', ';', ':']:
            continue

        texto_token = token.text.strip()

        if texto_token in stopwords_basicas:
            continue

        if len(texto_token) == 1 and not texto_token.isdigit():
            continue

        tokens.append(texto_token)

    texto_limpio = " ".join(tokens)

    return {
        "tokens": tokens,
        "texto_limpio": texto_limpio,
        "texto_normalizado": texto,
        "model": NLP_MODEL_NAME,
    }


import re as _re_signals

REGEX_CORREO = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}"
REGEX_URL = r"(https?://|www\.)[^\s<>\"']+"

# Regex de teléfonos para países hispanohablantes.
REGEX_TELEFONO = _re_signals.compile(r"""
    (\+34\s?\d{3}[\s.-]?\d{3}[\s.-]?\d{3})|
    (\+52\s?\d{10})|
    (\+54\s?\d{10})|
    (\+57\s?\d{10})|
    (\+56\s?\d{9})|
    (\+51\s?\d{9})|
    (\+58\s?\d{10})|
    (\+593\s?\d{9})|
    (\+502\s?\d{8})|
    (\+53\s?\d{8})|
    (\+591\s?\d{8})|
    (\+1-(809|829|849)[\s.-]?\d{3}[\s.-]?\d{4})|
    (\+504\s?\d{8})|
    (\+595\s?\d{9})|
    (\+503\s?\d{8})|
    (\+505\s?\d{8})|
    (\+506\s?\d{8})|
    (\+1-(787|939)[\s.-]?\d{3}[\s.-]?\d{4})|
    (\+598\s?\d{8})|
    (\+507\s?\d{8})
""", _re_signals.VERBOSE)

PALABRAS_URGENCIA = [
    "urgente",
    "urgencia",
    "rápido",
    "ya",
    "inmediato",
    "incorporación inmediata",
    "incorporación urgente",
    "disponibilidad inmediata",
    "empieza ya",
    "lo antes posible",
    "contratación inmediata",
    "entrevista hoy",
    "plazas limitadas",
    "últimas plazas",
    "solo hoy",
    "sin demora",
    "cuanto antes",
    "proceso express",
]
PALABRAS_SOSPECHOSAS = [
    "ganancias",
    "fácil",
    "sin experiencia",
    "pago previo",
    "transferencia",
    "ingresos rápidos",
    "dinero fácil",
    "trabaja desde casa",
    "sin titulación",
    "sin estudios",
    "sin papeles",
    "gana dinero",
    "comisiones altas",
    "100% comisión",
    "multinivel",
    "inversión inicial",
    "depósito previo",
    "datos bancarios",
    "cuenta bancaria",
    "western union",
    "bizum previo",
]

FUENTES_NO_FIABLES = ["facebook", "whatsapp", "telegram", "instagram", "tiktok", "snapchat"]
FUENTES_FIABLES = ["linkedin", "infojobs", "indeed", "glassdoor", "tecnoempleo", "computrabajo"]


# "Senales" es la información detectada en el texto.
# "Caracteristicas" son valores más estructurados para análisis posterior.
def _normalizar_senales(texto: str) -> str:
    texto = texto.lower()
    return _re_signals.sub(r"(?<=[a-záéíóúüñ])[.\-_](?=[a-záéíóúüñ])", "", texto)


def tiene_email(texto: str) -> int:
    return int(bool(_re_signals.search(REGEX_CORREO, texto, _re_signals.IGNORECASE)))


def tiene_telefono(texto: str) -> int:
    return int(bool(REGEX_TELEFONO.search(texto)))


def tiene_url(texto: str) -> int:
    return int(bool(_re_signals.search(REGEX_URL, texto, _re_signals.IGNORECASE)))


def puntuacion_urgencia(texto: str) -> int:
    texto = _normalizar_senales(texto)
    return sum(palabra in texto for palabra in PALABRAS_URGENCIA)


def palabras_sospechosas(texto: str) -> int:
    texto = _normalizar_senales(texto)
    return sum(palabra in texto for palabra in PALABRAS_SOSPECHOSAS)


def extraer_sospechosas(texto: str) -> list[str]:
    texto = _normalizar_senales(texto)
    return [palabra for palabra in PALABRAS_SOSPECHOSAS if palabra in texto]


def num_exclamaciones(texto: str) -> int:
    return texto.count("!")


def num_interrogaciones(texto: str) -> int:
    return texto.count("?")


def longitud_texto(texto: str) -> int:
    return len(texto)


def num_palabras(texto: str) -> int:
    return len(texto.split())


def num_oraciones(texto: str) -> int:
    coincidencias = _re_signals.findall(r"[.!?]+", texto)
    return len(coincidencias) if coincidencias else int(bool(texto.strip()))


def longitud_media_palabra(texto: str) -> float:
    palabras = _re_signals.findall(r"\b\w+\b", texto, _re_signals.UNICODE)
    if not palabras:
        return 0.0
    return round(sum(len(palabra) for palabra in palabras) / len(palabras), 2)


def num_urls(texto: str) -> int:
    return len(extraer_urls(texto))


def tiene_dinero(texto: str) -> int:
    return int(bool(_re_signals.search(r"(\d+\s?[€$])|([€$]\s?\d+)", texto)))


def proporcion_mayusculas(texto: str) -> float:
    letras = [caracter for caracter in texto if caracter.isalpha()]
    if not letras:
        return 0.0
    mayusculas = sum(1 for caracter in letras if caracter.isupper())
    return round(mayusculas / len(letras), 2)


def extraer_correos(texto: str) -> list[str]:
    return _re_signals.findall(REGEX_CORREO, texto, _re_signals.IGNORECASE)


def extraer_telefonos(texto: str) -> list[str]:
    coincidencias = REGEX_TELEFONO.findall(texto)
    telefonos = []
    for tupla in coincidencias:
        telefono_valido = next((valor for valor in tupla if valor), None)
        if telefono_valido:
            telefonos.append(telefono_valido)
    return telefonos


def extraer_urls(texto: str) -> list[str]:
    return _re_signals.findall(REGEX_URL, texto, _re_signals.IGNORECASE)


def extraer_empresas(texto: str) -> list[str]:
    doc = nlp(texto)
    return list({ent.text for ent in doc.ents 
                if ent.label_ == "ORG" and len(ent.text) > 3})


def extraer_lugares(texto: str) -> list[str]:
    doc = nlp(texto)
    return list({ent.text for ent in doc.ents 
                if ent.label_ in ("LOC", "GPE") and len(ent.text) > 3})


def extraer_urgencia(texto: str) -> list[str]:
    texto = _normalizar_senales(texto)
    return [palabra for palabra in PALABRAS_URGENCIA if palabra in texto]


def advertencias_telefonos(texto: str) -> list[str]:
    advertencias = []
    for telefono in extraer_telefonos(texto):
        if not telefono.startswith("+34"):
            advertencias.append(
                f"Cuidado: el número {telefono} no pertenece a España."
            )
    return advertencias


def evaluar_fuente_trabajo(texto: str) -> str:
    texto_minusculas = texto.lower()
    for fuente in FUENTES_NO_FIABLES:
        if fuente in texto_minusculas:
            return f"Cuidado! oferta encontrada en {fuente}. Puede no ser fiable."
    for fuente in FUENTES_FIABLES:
        if fuente in texto_minusculas:
            return f"Oferta encontrada en {fuente}. Plataforma más fiable."
    return "No se pudo determinar la fiabilidad de la fuente."


def extraer_caracteristicas(texto: str) -> dict:
    return {
        "tiene_email": tiene_email(texto),
        "tiene_telefono": tiene_telefono(texto),
        "tiene_url": tiene_url(texto),
        "num_urls": num_urls(texto),
        "tiene_dinero": tiene_dinero(texto),
        "puntuacion_urgencia": puntuacion_urgencia(texto),
        "palabras_sospechosas": palabras_sospechosas(texto),
        "longitud_texto": longitud_texto(texto),
        "num_palabras": num_palabras(texto),
        "num_exclamaciones": num_exclamaciones(texto),
        "num_interrogaciones": num_interrogaciones(texto),
        "num_oraciones": num_oraciones(texto),
        "longitud_media_palabra": longitud_media_palabra(texto),
        "proporcion_mayusculas": proporcion_mayusculas(texto),
    }


def extraer_senales(texto: str) -> dict:
    return {
        "correos": extraer_correos(texto),
        "telefonos": extraer_telefonos(texto),
        "urls": extraer_urls(texto),
        "empresas": extraer_empresas(texto),
        "lugares": extraer_lugares(texto),
        "fuente": evaluar_fuente_trabajo(texto),
        "expresiones_urgencia": extraer_urgencia(texto),
        "palabras_sospechosas": extraer_sospechosas(texto),
        "advertencias": advertencias_telefonos(texto),
    }


# Extractor principal: trafilatura — especializado en extraer el contenido principal
# de artículos y páginas web, ignorando menús, publicidad y ruido.
# Fallback: BeautifulSoup — extracción básica del texto visible del HTML cuando
# trafilatura no consigue resultados útiles.

# Dominios bloqueados: redes sociales que requieren login o bloquean scrapers.
blacklist_dominios = ["linkedin.com", "facebook.com", "tiktok.com", "instagram.com"]


def _normalize_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="La URL no es válida.")

    domain = (parsed.hostname or "").lower()
    if not domain:
        raise HTTPException(status_code=400, detail="La URL no es válida.")

    return url, domain


def _build_result(url: str, domain: str, title: str, text: str) -> dict[str, Any]:
    return {
        "success": True,
        "source": "url",
        "url": url,
        "domain": domain,
        "title": title,
        "text": text,
    }

config = use_config()
config.set("DEFAULT", "ROBOTS_TXT", "true")  # Respetar robots.txt"
def extract_from_url(url: str) -> dict[str, Any]:
    """
    Extrae el contenido textual principal desde una URL.
    """
    url_limpia, dominio = _normalize_url(url)

    # Comprobamos si el dominio está en la lista negra
    es_prohibida = any(dominio.endswith(sitio) for sitio in blacklist_dominios)
    if es_prohibida:
        raise HTTPException(status_code=403, detail="Dominio no permitido.")

    # Intento principal con trafilatura
    html = fetch_url(url_limpia, config=config)

    if html:
        # Pedimos la salida en JSON para acceder al texto y al título de forma estructurada
        resultado_json = extract(html, output_format="json")
        if resultado_json:
            datos = json.loads(resultado_json)
            texto = datos.get("text", "")
            if texto and texto.strip():
                return _build_result(url_limpia, dominio, datos.get("title", ""), texto)

    # Fallback con BeautifulSoup: se usa cuando trafilatura no extrae texto válido.
    # Eliminamos scripts, estilos y noscript antes de sacar el texto visible.
    try:
        response = requests.get(url_limpia, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Limpiamos etiquetas que no aportan contenido legible
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        texto = soup.get_text(separator=" ")
        texto = " ".join(texto.split())  # Colapsamos espacios y saltos de línea
        if not texto:
            raise HTTPException(status_code=422, detail="La URL no contiene texto legible.")

        return _build_result(url_limpia, dominio, "", texto)
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo acceder o procesar la URL.")


def ingest_text(text: str) -> dict:
    """
    Recibe texto manual y devuelve estructura base.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "success": False,
            "source": "text",
            "text": "",
            "message": "No se recibió texto válido."
        }

    return {
        "success": True,
        "source": "text",
        "text": text.strip(),
        "message": "Texto recibido correctamente."
    }

def ingest_image(file_bytes: bytes) -> dict:
    """
    Extrae texto de una imagen mediante OCR y devuelve estructura base.
    """
    resultado = extraer_texto(file_bytes)
    
    if resultado["status"] == "error":
        return {
            "success": False,
            "source": "imagen",
            "text": "",
            "message": resultado.get("message", "Error al procesar la imagen.")
        }
    
    texto = resultado.get("text", "").strip()
    if not texto:
        return {
            "success": False,
            "source": "imagen",
            "text": "",
            "message": "La imagen no contiene texto legible."
        }
    
    return {
        "success": True,
        "source": "imagen",
        "text": texto,
        "message": "Texto extraído correctamente."
    }

async def validar_entrada_traduccion(
    target_lang: str,
    file: UploadFile | None = None,
    text: str | None = None,
    url: str | None = None,
) -> dict:
    if not file and not text and not url:
        raise HTTPException(
            status_code=400,
            detail="Se debe proporcionar imagen, texto o URL.",
        )

    if sum(valor is not None for valor in [file, text, url]) > 1:
        raise HTTPException(
            status_code=400,
            detail="Proporciona solo una entrada: imagen, texto o URL.",
        )

    texto_para_traducir = ""
    entrada_detectada = ""

    if text:
        texto_para_traducir = text.strip()
        entrada_detectada = "texto"
    elif url:
        texto_para_traducir = url.strip()
        entrada_detectada = "url"
    elif file:
        entrada_detectada = "imagen"
        file_bytes = await file.read()          # ← lee los bytes reales
        ingesta = ingest_image(file_bytes)      # ← extrae el texto con OCR
        if not ingesta["success"]:
            raise HTTPException(
                status_code=422,
                detail=ingesta.get("message", "No se pudo extraer texto de la imagen."),
            )
        texto_para_traducir = ingesta["text"]   # ← texto OCR, no el filename

    if not texto_para_traducir.strip():
        raise HTTPException(
            status_code=422,
            detail="No se detectó contenido legible para traducir.",
        )

    if entrada_detectada == "texto" and len(texto_para_traducir.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="El texto es demasiado corto para detectar el idioma.",
        )

    return {
        "valido": True,
        "idioma_destino": target_lang,
        "entrada_detectada": entrada_detectada,
        "texto_para_traducir": texto_para_traducir,
        "mensaje": "Entrada válida para traducción.",
    }


MINIMO_PALABRAS_ANALISIS = 30


# Este archivo coordina el flujo completo: conecta módulos ya hechos
# y evita mezclar aquí la lógica concreta de limpieza, regex o extracción.
def construir_estadisticas(tokens: list[str], texto_limpio: str) -> dict:
    return {
        "tokens_totales": len(tokens),
        "palabras_unicas": len(set(tokens)),
        "longitud_texto_limpio": len(texto_limpio.split()),
    }


def construir_resultado(
    *,
    exito: bool,
    fuente: str,
    texto_original: str,
    texto_limpio: str,
    texto_normalizado: str,
    tokens: list[str],
    senales: dict,
    caracteristicas: dict,
    estadisticas: dict,
    metadatos: dict,
) -> dict:
    return {
        "exito": exito,
        "fuente": fuente,
        "texto_original": texto_original,
        "texto_limpio": texto_limpio,
        "texto_normalizado": texto_normalizado,
        "tokens": tokens,
        "senales": senales,
        "caracteristicas": caracteristicas,
        "estadisticas": estadisticas,
        "metadatos": metadatos,
    }


def _resultado_texto_insuficiente(
    *,
    fuente: str,
    texto_original: str,
    texto_limpio: str,
    texto_normalizado: str,
    tokens: list[str],
    estadisticas: dict,
    metadatos_extra: dict | None = None,
) -> dict:
    metadatos = {
        "mensaje": (
            f"Texto insuficiente para análisis. "
            f"Solo {estadisticas['longitud_texto_limpio']} palabras."
        ),
        "listo_para_analisis": False,
    }
    if metadatos_extra:
        metadatos.update(metadatos_extra)

    return construir_resultado(
        exito=False,
        fuente=fuente,
        texto_original=texto_original,
        texto_limpio=texto_limpio,
        texto_normalizado=texto_normalizado,
        tokens=tokens,
        senales={},
        caracteristicas={},
        estadisticas=estadisticas,
        metadatos=metadatos,
    )


def process_text_input(text: str) -> dict:
    """
    Ejecuta el pipeline completo para texto manual.
    """
    ingesta = ingest_text(text)

    if not ingesta["success"]:
        return construir_resultado(
            exito=False,
            fuente="texto",
            texto_original="",
            texto_limpio="",
            texto_normalizado="",
            tokens=[],
            senales={},
            caracteristicas={},
            estadisticas={
                "tokens_totales": 0,
                "palabras_unicas": 0,
                "longitud_texto_limpio": 0,
            },
            metadatos={
                "mensaje": ingesta.get("message", "Entrada no válida"),
                "listo_para_analisis": False,
            },
        )

    limpieza = clean_text(ingesta["text"])
    estadisticas = construir_estadisticas(limpieza["tokens"], limpieza["texto_limpio"])

    if estadisticas["longitud_texto_limpio"] <= MINIMO_PALABRAS_ANALISIS:
        return _resultado_texto_insuficiente(
            fuente="texto",
            texto_original=ingesta["text"],
            texto_limpio=limpieza["texto_limpio"],
            texto_normalizado=limpieza["texto_normalizado"],
            tokens=limpieza["tokens"],
            estadisticas=estadisticas,
            metadatos_extra={"modelo_limpieza": limpieza.get("model", "")},
        )

    return construir_resultado(
        exito=True,
        fuente="texto",
        texto_original=ingesta["text"],
        texto_limpio=limpieza["texto_limpio"],
        texto_normalizado=limpieza["texto_normalizado"],
        tokens=limpieza["tokens"],
        senales=extraer_senales(ingesta["text"]),
        caracteristicas=extraer_caracteristicas(ingesta["text"]),
        estadisticas=estadisticas,
        metadatos={
            "mensaje": "Procesamiento completado",
            "listo_para_analisis": True,
            "modelo_limpieza": limpieza.get("model", ""),
        },
    )


def process_url_input(url: str) -> dict:
    """
    Ejecuta el pipeline completo para entrada mediante URL.
    """
    extraccion = extract_from_url(url)
    limpieza = clean_text(extraccion["text"])
    estadisticas = construir_estadisticas(limpieza["tokens"], limpieza["texto_limpio"])
    metadatos_url = {
        "url": extraccion["url"],
        "dominio": extraccion.get("domain", ""),
        "titulo": extraccion.get("title", ""),
        "modelo_limpieza": limpieza.get("model", ""),
    }

    if estadisticas["longitud_texto_limpio"] <= MINIMO_PALABRAS_ANALISIS:
        return _resultado_texto_insuficiente(
            fuente="url",
            texto_original=extraccion["text"],
            texto_limpio=limpieza["texto_limpio"],
            texto_normalizado=limpieza["texto_normalizado"],
            tokens=limpieza["tokens"],
            estadisticas=estadisticas,
            metadatos_extra=metadatos_url,
        )

    return construir_resultado(
        exito=True,
        fuente="url",
        texto_original=extraccion["text"],
        texto_limpio=limpieza["texto_limpio"],
        texto_normalizado=limpieza["texto_normalizado"],
        tokens=limpieza["tokens"],
        senales=extraer_senales(extraccion["text"]),
        caracteristicas=extraer_caracteristicas(extraccion["text"]),
        estadisticas=estadisticas,
        metadatos={
            **metadatos_url,
            "mensaje": "Procesamiento completado",
            "listo_para_analisis": True,
        },
    )

def process_image_input(file_bytes: bytes) -> dict:
    """
    Ejecuta el pipeline completo para entrada mediante imagen (OCR).
    """
    ingesta = ingest_image(file_bytes)

    if not ingesta["success"]:
        return construir_resultado(
            exito=False,
            fuente="imagen",
            texto_original="",
            texto_limpio="",
            texto_normalizado="",
            tokens=[],
            senales={},
            caracteristicas={},
            estadisticas={
                "tokens_totales": 0,
                "palabras_unicas": 0,
                "longitud_texto_limpio": 0,
            },
            metadatos={
                "mensaje": ingesta.get("message", "Entrada no válida"),
                "listo_para_analisis": False,
            },
        )

    limpieza = clean_text(ingesta["text"])
    estadisticas = construir_estadisticas(limpieza["tokens"], limpieza["texto_limpio"])

    if estadisticas["longitud_texto_limpio"] <= MINIMO_PALABRAS_ANALISIS:
        return _resultado_texto_insuficiente(
            fuente="imagen",
            texto_original=ingesta["text"],
            texto_limpio=limpieza["texto_limpio"],
            texto_normalizado=limpieza["texto_normalizado"],
            tokens=limpieza["tokens"],
            estadisticas=estadisticas,
            metadatos_extra={"modelo_limpieza": limpieza.get("model", "")},
        )

    return construir_resultado(
        exito=True,
        fuente="imagen",
        texto_original=ingesta["text"],
        texto_limpio=limpieza["texto_limpio"],
        texto_normalizado=limpieza["texto_normalizado"],
        tokens=limpieza["tokens"],
        senales=extraer_senales(ingesta["text"]),
        caracteristicas=extraer_caracteristicas(ingesta["text"]),
        estadisticas=estadisticas,
        metadatos={
            "mensaje": "Procesamiento completado",
            "listo_para_analisis": True,
            "modelo_limpieza": limpieza.get("model", ""),
        },
    )


class EntradaTexto(BaseModel):
    text: str = Field(..., min_length=1, description="Texto manual para procesar.")


class EntradaURL(BaseModel):
    url: HttpUrl = Field(..., description="URL pública desde la que se extraerá el texto.")


class ResultadoProcesamiento(BaseModel):
    exito: bool
    fuente: str
    texto_original: str
    texto_limpio: str
    texto_normalizado: str
    tokens: List[str]
    senales: Dict[str, Any]
    caracteristicas: Dict[str, Any]
    estadisticas: Dict[str, Any]
    metadatos: Optional[Dict[str, Any]] = None


class ResultadoValidacionTraduccion(BaseModel):
    valido: bool
    idioma_destino: str
    entrada_detectada: str
    texto_para_traducir: str
    mensaje: str

