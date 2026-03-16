from pydantic import BaseModel
from typing import Optional
from enum import Enum

# Definición de modelos de datos para la aplicación

#Modelo de datos para el semáforo
class NivelSeguridad(str, Enum):
    VERDE = bool
    AMARILLO = bool   
    ROJO = bool

#Modelo para determinar la clase de entrada del usuario
class TipoEntrada(str, Enum):
    TEXTO = bool
    IMAGEN = bool
    ENLACE = bool
#Modelo de datos para la entrada del mensaje del usuario
class AnuncioEntrada(BaseModel):
    tipo : TipoEntrada
    texto: str
    idioma: Optional[str] = "es"  # Idioma del texto, por defecto español

#Modelo de datos para la respuesta del análisis
class ResultadoAnalisis(BaseModel):
    tipo_entrada: TipoEntrada
    nivel_seguridad: NivelSeguridad
    confianza_seguridad: float
    mensaje: str
    indicadores: list[str]
    idioma_detectado: str

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
    texto: str
    idioma: Optional[str] = "es"  # Idioma del texto, por defecto español

#Modelo para la respuesta de la detección de idioma
class ResultadoDeteccion(BaseModel):
    idioma_detectado: str
    es_analizable: bool
    mensaje: str
