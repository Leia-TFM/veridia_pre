from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import os
import sys
import json
import logging

# --- Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición) ---
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

from api.models.schemas import AnuncioEntrada, TipoEntrada, ResultadoAnalisis, NivelSeguridad
from api.config import settings

# Importar servicios
from servicios.traduccion_service import traducir_contenido
from servicios.ia_service import OrquestadorAgente, validar_anuncio
from servicios.data_service import guardar_datos

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Instancia global del orquestador (lazy loading)
_orquestador = None


def _get_orquestador():
    """Obtiene o crea la instancia del orquestador de IA."""
    global _orquestador
    if _orquestador is None:
        pipeline_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models",
            "modelo_hibrido_prueba.pkl"
        )
        # Si no existe el pipeline, usamos modo sin ML
        if not os.path.exists(pipeline_path):
            logger.warning(f"Pipeline de ML no encontrado en {pipeline_path}, usando modo texto")
            _orquestador = None
        else:
            _orquestador = OrquestadorAgente(
                pipeline_path=pipeline_path,
                model_id=settings.MODELO,
                max_steps=6
            )
    return _orquestador


async def _procesar_y_analizar(texto_original: str, translated: str, idioma_detectado: str, tipo: TipoEntrada) -> ResultadoAnalisis:
    """
    Procesa el texto y lo analiza mediante el agente de IA.
    Retorna el resultado del análisis.
    """
    # Limpiar y preparar el texto para análisis
    from servicios.texto_service import clean_text
    
    # Usar el texto traducido si está en español, si no el original
    texto_para_analisis = translated if idioma_detectado == "es" else texto_original
    
    # Limpiar texto
    resultado_limpio = clean_text(texto_para_analisis)
    texto_limpio = resultado_limpio.get("texto_limpio", texto_para_analisis)
    
    # Validar estructura del anuncio
    try:
        data_validada = await validar_anuncio({
            "descripcion": texto_limpio,
            "url_oferta": None
        })
    except Exception as e:
        logger.warning(f"Error en validación: {e}")
        data_validada = {"descripcion": texto_limpio}
    
    # Obtener orquestador
    orquestador = _get_orquestador()
    
    if orquestador:
        # Usar agente IA para análisis
        try:
            # Convertir a JSON para el agente
            job_posting_json = json.dumps(data_validada, ensure_ascii=False)
            resultado_ia = orquestador.ejecutar_tarea(job_posting_json)
            
            logger.info(f"Resultado raw del agente: {resultado_ia[:500]}")

            # Parsear resultado del agente
            return _parsear_resultado_ia(resultado_ia, tipo, idioma_detectado)
        except Exception as e:
            logger.error(f"Error en análisis IA: {e}")
            # Fallback a análisis por reglas
            return _analisis_por_reglas(texto_limpio, tipo, idioma_detectado)
    else:
        # Fallback: análisis por reglas simples
        return _analisis_por_reglas(texto_limpio, tipo, idioma_detectado)


def _parsear_resultado_ia(resultado: str, tipo: TipoEntrada, idioma_detectado: str) -> ResultadoAnalisis:
    """
    Parsea el resultado del agente de IA y lo convierte al formato de respuesta.
    """
    import re

    # Intentar parsear directamente
    data = None
    try:
        data = json.loads(resultado)
    except json.JSONDecodeError:
        # El agente devuelve texto libre con JSON embebido — extraerlo
        match = re.search(r'\{.*\}', resultado, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.warning(f"Error al parsear JSON extraído: {e}, usando análisis por reglas")
        else:
            logger.warning(f"No se encontró JSON en resultado IA: {resultado[:200]}")

    if data is None:
        return _analisis_por_reglas(resultado, tipo, idioma_detectado)

    try:
        # Mapear veredicto a nivel de seguridad
        veredicto = data.get("verdict", "").upper()
        if veredicto == "FRAUDULENT":
            nivel = NivelSeguridad.ROJO
        elif veredicto == "LEGITIMATE":
            nivel = NivelSeguridad.VERDE
        else:
            nivel = NivelSeguridad.AMARILLO

        senales = data.get("senales") or []
        indicadores = data.get("caracteristicas") or []

        if not indicadores and senales:
            indicadores = senales
            
        # Confianza basada en el nivel de certeza
        probabilidad = data.get("probability", data.get("probabilidad", 0.5))
        confianza = float(probabilidad) if isinstance(probabilidad, (int, float)) else 0.5

        # Nivel de confianza (high/medium/low)
        nivel_confianza = data.get("confidence_level", data.get("confianza", "medium"))

        justificacion = data.get("justificacion") or ""
        mensaje = justificacion

        return ResultadoAnalisis(
            tipo_entrada=tipo,
            nivel_seguridad=nivel,
            confianza_seguridad=confianza,
            probabilidad=confianza,
            justificacion=justificacion,
            mensaje=mensaje,
            indicadores=indicadores if isinstance(indicadores, list) else [str(indicadores)],
            idioma_detectado=idioma_detectado,
            nivel_confianza=nivel_confianza,
            senales=senales if isinstance(senales, list) else [],
            caracteristicas=data.get("caracteristicas", {}),
            veredicto=veredicto
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Error al construir ResultadoAnalisis: {e}, usando análisis por reglas")
        return _analisis_por_reglas(resultado, tipo, idioma_detectado)


def _analisis_por_reglas(texto: str, tipo: TipoEntrada, idioma_detectado: str) -> ResultadoAnalisis:
    """
    Análisis por reglas simples como fallback.
    """
    from servicios.texto_service import (
        puntuacion_urgencia,
        palabras_sospechosas,
        extraer_sospechosas,
        tiene_email,
        tiene_telefono,
        tiene_url
    )
    
    # Calcular indicadores de sospecha
    score_urgencia = puntuacion_urgencia(texto)
    score_sospechosas = palabras_sospechosas(texto)
    lista_sospechosas = extraer_sospechosas(texto)
    
    # Indicadores encontrados
    indicadores = []
    
    if score_urgencia > 0:
        indicadores.append("Lenguaje de urgencia excesiva")
    if score_sospechosas > 0:
        indicadores.extend(lista_sospechosas)
    if not tiene_email(texto) and not tiene_telefono(texto):
        indicadores.append("Sin datos de contacto verificables")
    
    # Determinar nivel según score
    if score_sospechosas >= 3 or score_urgencia >= 3:
        nivel = NivelSeguridad.ROJO
        confianza = 0.85
    elif score_sospechosas >= 1 or score_urgencia >= 1:
        nivel = NivelSeguridad.AMARILLO
        confianza = 0.65
    else:
        nivel = NivelSeguridad.VERDE
        confianza = 0.75
    
    # Mensaje según nivel
    mensajes = {
        NivelSeguridad.VERDE: "El anuncio no presenta señales evidentes de riesgo.",
        NivelSeguridad.AMARILLO: "El anuncio presenta algunas señales que requieren precaución.",
        NivelSeguridad.ROJO: "El anuncio presenta múltiples señales de posible fraude."
    }
    
    return ResultadoAnalisis(
        tipo_entrada=tipo,
        nivel_seguridad=nivel,
        confianza_seguridad=confianza,
        probabilidad=confianza,  
        justificacion=mensajes[nivel],  
        indicadores=indicadores,
        idioma_detectado=idioma_detectado,
        veredicto="FRAUDULENT" if nivel.name == "ROJO" else "LEGITIMATE",
    )


@router.post("/analizar", response_model=ResultadoAnalisis)
async def analizar_anuncio(anuncio: AnuncioEntrada = Depends(AnuncioEntrada.as_form), file: UploadFile = File(None)):
    """
    Endpoint principal para analizar anuncios laborales.
    
    Flujo determinista:
    1. Determinar tipo de entrada (URL, IMAGEN o TEXTO)
    2. Extraer texto según tipo (web scraping, OCR o texto directo)
    3. Detectar idioma y traducir al idioma destino
    4. Analizar mediante agente de IA
    5. Devolver resultado al frontend
    """
    logger.info(f"Iniciando análisis - Tipo: {anuncio.tipo}, Idioma destino: {anuncio.idioma_destino}")
    
    # Determinar tipo de entrada y obtener contenido
    if anuncio.tipo == TipoEntrada.IMAGEN:
        # Verificar que se proporcionó archivo
        if not file:
            raise HTTPException(status_code=400, detail="Se requiere archivo de imagen para tipo IMAGEN")
        
        # Procesar imagen -> OCR -> texto
        try:
            original, translated, idioma_detectado = await traducir_contenido(
                target_lang=anuncio.idioma_destino,
                file=file,
                text=None,
                url=None
            )
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            raise HTTPException(status_code=422, detail=f"Error al procesar imagen: {str(e)}")
    
    elif anuncio.tipo == TipoEntrada.ENLACE:
        # Verificar que se proporcionó URL
        if not anuncio.url:
            raise HTTPException(status_code=400, detail="Se requiere URL para tipo ENLACE")
        
        # Procesar URL -> web scraping -> texto
        try:
            original, translated, idioma_detectado = await traducir_contenido(
                target_lang=anuncio.idioma_destino,
                file=None,
                text=None,
                url=anuncio.url
            )
        except Exception as e:
            logger.error(f"Error procesando URL: {e}")
            raise HTTPException(status_code=422, detail=f"Error al procesar URL: {str(e)}")
    
    else:  # TipoEntrada.TEXTO
        # Verificar que se proporcionó texto
        if not anuncio.texto:
            raise HTTPException(status_code=400, detail="Se requiere texto para tipo TEXTO")
        
        # Procesar texto directo
        try:
            original, translated, idioma_detectado = await traducir_contenido(
                target_lang=anuncio.idioma_destino,
                file=None,
                text=anuncio.texto,
                url=None
            )
        except Exception as e:
            logger.error(f"Error procesando texto: {e}")
            raise HTTPException(status_code=422, detail=f"Error al procesar texto: {str(e)}")
    
    # Verificar que se obtuvo contenido
    if not original or not original.strip():
        raise HTTPException(status_code=422, detail="No se pudo extraer contenido del anuncio")
    
    logger.info(f"Contenido extraído - Idioma: {idioma_detectado}, Caracteres: {len(original)}")
    
    # Análisis mediante IA
    resultado = await _procesar_y_analizar(original, translated, idioma_detectado, anuncio.tipo)

    # Guardar registro de análisis para entrenamiento/finetuning posterior
    try:
        guardar_datos(
            anuncio=anuncio.dict(),
            original_text=original,
            translated_text=translated,
            idioma_detectado=idioma_detectado,
            resultado=resultado.dict()
        )
    except Exception as e:
        logger.warning(f"No se pudo guardar registro de análisis: {e}")
    
    logger.info(f"Análisis completado - Nivel: {resultado.nivel_seguridad}, Confianza: {resultado.confianza_seguridad}")
    
    return resultado
