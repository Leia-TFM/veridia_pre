from pydantic import BaseModel
from typing import Optional
from enum import Enum
from fastapi import Form

# Definición de modelos de datos para la aplicación

# Enum con los idiomas disponibles en la interfaz.
# El valor de cada opción es su código ISO 639-1, que es el que consume directamente GoogleTranslator.
# Se han añadido idiomas relevantes para el perfil de usuario del proyecto:
#   - Lenguas cooficiales españolas (catalán)
#   - Idiomas de las comunidades migrantes más numerosas en España (ucraniano, polaco, rumano...)
#   - Idiomas de principales países de origen de víctimas de trata (árabe)
class TargetLanguage(str, Enum):
    # Europa occidental
    english    = "en"
    spanish    = "es"
    french     = "fr"
    german     = "de"
    portuguese = "pt"
    italian    = "it"
    dutch      = "nl"
    catalan    = "ca"
   
    # Europa del este / norte
    russian    = "ru"
    polish     = "pl"
    ukrainian  = "uk"
    romanian   = "ro"   # añadido por Carmen
   
    # Oriente Medio / África
    arabic     = "ar"
    
#Modelo de datos para el semáforo
class NivelSeguridad(str, Enum):
    VERDE = "verde"
    AMARILLO = "amarillo"   
    ROJO = "rojo"

#Modelo para determinar la clase de entrada del usuario
class TipoEntrada(str, Enum):
    TEXTO = "TEXTO"
    IMAGEN = "IMAGEN"
    ENLACE = "ENLACE"

#Modelo de datos para la entrada del mensaje del usuario
class AnuncioEntrada(BaseModel):
    texto: Optional[str] = None
    url: Optional[str] = None
    idioma_destino:  TargetLanguage
    tipo: TipoEntrada 

    @classmethod
    def as_form(
        cls,
        texto: Optional[str] = Form(None),
        url: Optional[str] = Form(None),
        idioma_destino:  TargetLanguage = Form(...),
        tipo: TipoEntrada = Form(...)
    ):
        return cls(texto=texto, url=url, idioma_destino=idioma_destino, tipo=tipo)

#Modelo de datos para la respuesta del análisis
class ResultadoAnalisis(BaseModel):
    tipo_entrada: TipoEntrada
    nivel_seguridad: NivelSeguridad
    confianza_seguridad: float
    justificacion: str
    mensaje: Optional[str] = None
    idioma_detectado: str
    # Campos adicionales del agente IA
    nivel_confianza: Optional[str] = None  # high/medium/low
    senales: Optional[list[str]] = None   # Señales detectadas
    caracteristicas: Optional[dict] = None # Características adicionales
    veredicto: Optional[str] = None        # FRAUDULENT/LEGITIMATE
    probabilidad: float

#Modelos    para las estadísticas generales
#Modelo para la distribución del semáforo
class DistribucionSemaforo(BaseModel):
    verde: int
    amarillo: int
    rojo: int

#Modelo para las estadísticas generales
class EstadisticasGenerales(BaseModel):
    total_analizados: int
    distribucion_semaforo: DistribucionSemaforo
    indicadores_frecuentes: dict[str, int]  # {"palabra": frecuencia}
    idiomas_frecuentes: dict[str, int]      # {"es": 45, "en": 12}


#Modelos para la detección de idioma y traducción

#Modelo para la entrada del texto a detectar
class TextoDetectar(BaseModel):
    texto: Optional[str] = None
    url: Optional[str] = None
    idioma_destino:  TargetLanguage 

    @classmethod
    def as_form(
        cls,
        texto: Optional[str] = Form(None),
        url: Optional[str] = Form(None),
        idioma_destino:  TargetLanguage = Form(...),
    ):
        return cls(texto=texto, url=url, idioma_destino=idioma_destino)

#Modelo para la respuesta de la detección de idioma
class ResultadoDeteccion(BaseModel):
    idioma_detectado: str
    es_analizable: bool
    mensaje: str
    original: str
    traducido: str
