"""
IA_SERVICE
========================================================

DESCRIPCIÓN FUNCIONAL:
Este módulo constituye el núcleo de inteligencia y seguridad del sistema. Su objetivo 
es orquestar la validación, sanitización y clasificación de anuncios de empleo 
mediante un enfoque híbrido de Machine Learning y Agentes de IA.

COMPONENTES CLAVE:
1. CAPA DE SEGURIDAD DEFENSIVA: Implementa filtros contra 'Prompt Injection' y 
'Code Injection', asegurando que el LLM no sea subvertido por entradas maliciosas. 
Incluye normalización Unicode NFC para mitigar ataques de homógrafos.
2. VALIDACIÓN ESTRUCTURAL (Pydantic V2): Gestiona la integridad de los datos mediante 
un esquema flexible (DTO) que soporta la variabilidad de los anuncios reales.
3. MOTOR DE INFERENCIA (FraudDetectionTool): Encapsula un pipeline de ML 
(BERT/XGBoost) con soporte para extracción de contenido vía URL (Scraping) 
o procesamiento de texto plano. Implementa Lazy Loading para eficiencia de memoria.
4. AGENTE ORQUESTADOR (ReAct): Utiliza un 'ToolCallingAgent' de smolagents que permite 
al sistema razonar sobre la consulta del usuario y decidir autónomamente el uso 
de las herramientas de detección.

TECNOLOGÍAS PRINCIPALES:
- Pydantic V2 (Validación de datos)
- Smolagents / Hugging Face (Arquitectura de Agentes)
- Scikit-learn / Joblib (Inferencia de ML)
- RE / Unicodedata (Seguridad y Normalización)

"""
import asyncio
import json
import re
import unicodedata
import httpx
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError
from smolagents import ToolCallingAgent, HfApiModel, Tool
from api.config import settings
from texto_service import process_text_input, process_url_input


# =============================================================================
# SECCIÓN 1 – CONSTANTES Y REGEX DE SEGURIDAD 
# =============================================================================

# Se definen umbrales máximos en bytes para prevenir ataques de Denegación de 
# Servicio (DoS) por agotamiento de memoria o desbordamiento de búfer 

MAX_BYTES_TITULO = 300
MAX_BYTES_DESCRIPCION = 8000

# Detección de 'Indirect Prompt Injection'
# -----------------------------------------------------------------------------
# Esta heurística mitiga ataques donde un atacante esconde instrucciones en la 
# oferta de empleo para subvertir el System Prompt del LLM.
# Se buscan patrones de secuestro de flujo como "ignore previous instructions",
# cambios de rol ("you are now"), o marcadores de chat templating (<|im_start|>) 
# que podrían inducir al modelo a un comportamiento no deseado o fuga de datos.

PROMPT_INJECTION_RE = re.compile(
    r"(ignore\s+(previous|all)\s+instructions?|"
    r"you\s+are\s+now\s+|act\s+as\s+|"
    r"jailbreak|DAN\s+mode|"
    r"system\s*:\s*|<\|im_start\|>|"
    r"\[INST\]|\[SYS\])",
    re.IGNORECASE,
)

# Prevención de Inyecciones de Código y Persistencia
# -----------------------------------------------------------------------------
# Defensa proactiva contra Cross-Site Scripting (XSS) y SQL Injection.
# Aunque el modelo de ML no ejecuta código, estos filtros protegen las capas 
# posteriores donde se almacenarán o mostrarán los resultados del análisis.

CODE_INJECTION_RE = re.compile(
    r"(<script[\s>]|</script>|javascript\s*:|"
    r"on\w+\s*=\s*[\"']|"
    r"vbscript\s*:|data\s*:\s*text/html|"
    r"'\s*;\s*DROP\s+TABLE|"
    r"--\s*$|1\s*=\s*1|'\s*OR\s*'1'\s*=\s*'1)",
    re.IGNORECASE,
)

# Mitigación de Ataques por Ofuscación Unicode
# -----------------------------------------------------------------------------
# Detecta caracteres de control no imprimibles (C0/C1 control sets) y caracteres 
# de formato invisible (como Zero-Width Spaces o marcas Bidi).
# Estos caracteres se utilizan frecuentemente para evadir filtros de texto, 
# romper la tokenización semántica del modelo de lenguaje o realizar ataques 
# visuales (homoglyphs) que engañan tanto al algoritmo como al usuario.

CONTROL_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|"
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064]"
)
# =============================================================================
# SECCIÓN 2 – FUNCIONES DE SANITIZACIÓN
# =============================================================================

def _normalize_unicode(value: str) -> str:
    """
    Normalización Canónica (NFC - Canonical Composition).
    -------------------------------------------------------------------------
    Técnica crítica para mitigar ataques de 'Homoglyphs' y asegurar la 
    consistencia del vocabulario antes de la tokenización. 
    Transforma caracteres combinados (como una 'e' y un acento combinable) 
    en su forma única precompuesta. Esto garantiza que el modelo de 
    NLP reciba una representación unívoca de los grafemas, evitando 
    la dispersión semántica en el espacio de embeddings.
    """
    return unicodedata.normalize("NFC", value)


def _sanitize(value: str, field_name: str = "campo") -> str:
    """
    Arquitectura de Pipeline de Limpieza Secuencial.
    -------------------------------------------------------------------------
    Implementa una estrategia de 'Fail-Fast' mediante una serie de filtros 
    jerárquicos. El orden es deliberado para optimizar el cómputo:
    
    1. Strip: Eliminación de ruido en los extremos (espacios, saltos de línea).
    2. Normalización NFC: Estandarización de la codificación Unicode.
    3. Validación de integridad:
    - Control Chars: Bloqueo de caracteres no imprimibles que podrían 
        corromper los buffers de procesamiento.
    - Code Injection: Defensa contra payloads maliciosos que apuntan a 
        la infraestructura (SQL/HTML).
    - Prompt Injection: Protección específica para la capa de IA, detectando  de ataque semántico 
        detectados en la Sección 1.
    """
    value = value.strip()
    value = _normalize_unicode(value)

    if CONTROL_CHARS_RE.search(value):
        raise ValueError(f"'{field_name}' contiene caracteres de control no permitidos.")
    if CODE_INJECTION_RE.search(value):
        raise ValueError(f"'{field_name}' contiene código HTML/SQL malicioso.")
    if PROMPT_INJECTION_RE.search(value):
        raise ValueError(f"'{field_name}' contiene instrucciones de inyección de IA.")

    return value


def _check_byte_size(value: str, max_bytes: int, field_name: str) -> str:
    """
    Validación de Restricción de Recursos (Resource Constraining).
    -------------------------------------------------------------------------
    A diferencia de len(str), que cuenta caracteres, esta función evalúa el 
    tamaño real en bytes (UTF-8). Es fundamental para:
    1. Prevenir ataques de denegación de servicio (DoS) por memoria.
    2. Asegurar la compatibilidad con los límites de contexto (Window Size) 
    del modelo de lenguaje y el pipeline de embeddings, evitando truncamientos 
    inesperados que degraden el rendimiento del clasificador.
    """
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"'{field_name}' supera el límite de {max_bytes} bytes.")
    return value
# =============================================================================
# SECCIÓN 3 – ESQUEMA PYDANTIC (JobAdInput)
# =============================================================================

class JobAdInput(BaseModel):
    """
    Data Transfer Object (DTO) basado en Pydantic V2.
    -------------------------------------------------------------------------
    Este modelo actúa como la 'Single Source of Truth' para la estructura de 
    un anuncio de empleo. Su diseño responde a tres principios arquitectónicos:
    
    1. Esquema de Tipado Débil pero Seguro: Se definen todos los campos como 
        'Optional' para maximizar la resiliencia frente a fuentes de datos 
        heterogéneas (Scraping, APIs externas, formularios manuales).
    2. Constraints de Dominio: Implementa restricciones físicas (max_length) 
        y lógicas (gt=0, lt=30_000 para salarios) que actúan como filtros de 
        calidad de datos previos a la inferencia.
    3. Extensibilidad Adaptativa: Mediante 'extra: allow', el modelo permite 
        la ingesta de metadatos adicionales no previstos, facilitando el 
        Future-Proofing del sistema de IA.
    """

    titulo:         Optional[str] = Field(default=None, max_length=120)
    empresa:        Optional[str] = Field(default=None, max_length=100)
    descripcion:    Optional[str] = Field(default=None, max_length=3000)
    salario_min:    Optional[float] = Field(default=None, gt=0, lt=30_000)
    salario_max:    Optional[float] = Field(default=None, gt=0, lt=30_000)
    jornada_horas:  Optional[int]   = Field(default=None, ge=1, le=60)
    ubicacion:      Optional[str]   = Field(default=None, max_length=100)
    contacto:       Optional[str]   = Field(default=None, max_length=100)
    tipo_contrato:  Optional[str]   = Field(default=None, max_length=60)
    url_oferta:     Optional[str]   = Field(default=None, max_length=300)

    model_config = {"extra": "allow"}

    @field_validator("titulo", "empresa", "descripcion",
                    "ubicacion", "tipo_contrato", "contacto", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v, info):
        """
        Interceptor de Validación 'Pre-Assignment'.
        ---------------------------------------------------------------------
        Utiliza el modo 'before' para sanitizar el contenido antes de que 
        Pydantic intente coercionar el tipo. Esto garantiza que cualquier 
        intento de inyección de código sea neutralizado en la fase de parseo, 
        impidiendo que datos maliciosos lleguen a instanciarse en el objeto.
        """
        if v is None:
            return v
        return _sanitize(str(v), field_name=info.field_name)

    @field_validator("descripcion", mode="after")
    @classmethod
    def descripcion_byte_limit(cls, v):
        """
        Interceptor de Validación 'Post-Assignment'.
        ---------------------------------------------------------------------
        Se ejecuta tras la sanitización para verificar que el volumen de datos 
        final (una vez normalizado el Unicode) no exceda los límites de 
        memoria establecidos para la ventana de contexto del modelo de NLP.
        """
        if v is None:
            return v
        return _check_byte_size(v, MAX_BYTES_DESCRIPCION, "descripcion")

# =============================================================================
# SECCIÓN 4 – ORQUESTADOR DE VALIDACIÓN
# =============================================================================

async def validar_anuncio(data: dict) -> dict:
    """
    Controlador de Validación Asíncrono (Input Gateway).
    -------------------------------------------------------------------------
    Esta función actúa como el punto de entrada lógico para la ingesta de datos. 
    Sus responsabilidades técnicas clave son:

    1. Inyección de Dependencias: Recibe un diccionario ('data') —típicamente 
        proveniente de un payload JSON de una petición HTTP— y lo somete al 
        contrato definido en 'JobAdInput'.
    2. Ejecución de Pipeline de Seguridad: Al instanciar 'JobAdInput', se 
        disparan automáticamente todos los validadores de campo (sanitización, 
        normalización Unicode y detección de inyecciones) definidos en la Sección 3.
    3. Naturaleza No Bloqueante (Async): Al estar definida como 'async', permite 
        que el orquestador gestione múltiples validaciones simultáneas sin 
        bloquear el 'Event Loop', algo crítico para la escalabilidad del sistema 
        bajo cargas elevadas de peticiones concurrentes.
    4. Serialización de Salida: Retorna un 'model_dump()', garantizando que el 
        diccionario resultante sea un objeto limpio, tipado y verificado, listo 
        para ser consumido por el modelo de Machine Learning.
    """
    # La instanciación realiza el 'parsing' y 'validation' simultáneamente.
    ad = JobAdInput(**data)
    
    # Exportación del modelo validado como diccionario estándar de Python.
    return ad.model_dump()

# =============================================================================
# SECCIÓN 5 – HELPER DE TEXTO
# =============================================================================

# Jerarquía de Relevancia Semántica
# -----------------------------------------------------------------------------
# Se establece un orden determinista de campos basado en su peso estadístico 
# para la detección de fraude. 
_CAMPOS_TEXTO = [
    "titulo", "empresa", "descripcion",
    "tipo_contrato", "ubicacion",
    "jornada_horas", "salario_min", "salario_max", "contacto",
]

def _campos_a_texto(fields: dict) -> str:
    """
    Motor de Transformación de Diccionario a Representación Lineal.
    -------------------------------------------------------------------------
    Esta función implementa una serialización inteligente para convertir el 
    objeto validado en un formato de texto plano estructurado. Sus objetivos son:

    1. Preservación de la Señal: Utiliza un formato "clave: valor" que ayuda a 
        los modelos de lenguaje a desambiguar el contexto de cada dato (ej. 
        diferenciar entre la ubicación de la empresa y el contacto).
    2. Manejo de Datos No Estructurados: Mediante el cálculo de la diferencia de 
        conjuntos (set difference), identifica y concatena dinámicamente campos 
        adicionales que no estaban en el esquema original, evitando la pérdida 
        de información 'ad-hoc'.
    3. Optimización del Context Window: Al filtrar valores nulos o vacíos antes 
        de la concatenación, se reduce el número de tokens innecesarios, 
        maximizando la eficiencia del modelo de inferencia.
    4. Determinismo: Ordena los campos extra alfabéticamente para garantizar 
        que la entrada al modelo sea reproducible, facilitando la auditoría y 
        el testeo del sistema.
    """
    partes = []
    
    # Inyección de campos conocidos siguiendo la jerarquía de pesos semánticos.
    for campo in _CAMPOS_TEXTO:
        valor = fields.get(campo)
        if valor is not None and str(valor).strip():
            partes.append(f"{campo}: {valor}")
    
    # Descubrimiento dinámico de atributos adicionales.
    # Excluimos 'url_oferta' ya que su procesamiento es ortogonal (vía scraping).
    campos_extra = set(fields.keys()) - set(_CAMPOS_TEXTO) - {"url_oferta"}
    for campo in sorted(campos_extra):
        valor = fields.get(campo)
        if valor is not None and str(valor).strip():
            partes.append(f"{campo}: {valor}")
    
    # Resultado: Una cadena multilínea que preserva la estructura lógica del anuncio.
    return "\n".join(partes)
# =============================================================================
# SECCIÓN 6 – TOOL DE DETECCIÓN DE MACHINE LEARNING 
# =============================================================================

class FraudDetectionTool(Tool):
    """
    Abstracción de Servicio de Detección (Patrón Command/Tool).
    -------------------------------------------------------------------------
    Esta clase encapsula la complejidad del pipeline de Machine Learning y lo 
    expone como una interfaz estándar para un Agente de IA.

    1. Firma de Herramienta (Prompt Engineering): La descripción y el esquema de 
        inputs no son solo comentarios; son los metadatos que el LLM lee para 
        entender 'cuándo' y 'cómo' invocar esta herramienta dentro de su ciclo 
        de razonamiento (ReAct).
    2. Lazy Loading (Carga Perezosa): El pipeline de ML solo se carga en memoria 
        mediante '_load_pipeline' en el momento de la primera inferencia. Esto 
        optimiza el tiempo de arranque de la aplicación y reduce el consumo de 
        memoria RAM en entornos de microservicios.
    3. Cuantificación de Incertidumbre: Mediante '_get_confidence_level', se 
        traduce la probabilidad continua (soft output) del modelo en niveles de 
        confianza discretos, facilitando la toma de decisiones por parte del 
        agente o del usuario final.
    """

    def forward(self, job_posting_json: str) -> str:
        """
        Ejecución del Pipeline de Predicción.
        ---------------------------------------------------------------------
        Sigue un flujo de procesamiento de tres etapas:
        
        1. Deserialización y Recuperación de Datos: Extrae los campos validados.
        2. Estrategia Híbrida de Adquisición de Texto: 
            - Si existe una URL, se delega al servicio 'process_url_input' para 
                realizar scraping dinámico y limpieza de HTML.
            - Si no, se utiliza la serialización semántica de la Sección 5.
        3. Inferencia Dual:
            - predict_proba: Para obtener la probabilidad de la clase positiva (Fraude).
            - predict: Para obtener la etiqueta binaria final.
        """
        
        self._load_pipeline()
        
        # El pipeline asume un texto normalizado como entrada (Tf-Idf/Embeddings).
        proba_fraud = float(self._pipeline.predict_proba([texto_para_modelo])[0][1])
        label       = int(self._pipeline.predict([texto_para_modelo])[0])

        # Retorno de un payload de información enriquecida (Enriched Results).
        return json.dumps({
            "verdict"         : "FRAUDULENT" if label == 1 else "LEGITIMATE",
            "probability"     : round(proba_fraud, 4),
            "confidence_level": self._get_confidence_level(proba_fraud),
            "fuente"          : resultado_proc["fuente"],
            "senales"         : resultado_proc["senales"], # Explicabilidad (XAI)
            "caracteristicas" : resultado_proc["caracteristicas"],
            "estadisticas"    : resultado_proc["estadisticas"],
        }, ensure_ascii=False)

    def __getstate__(self):
        """
        Gestión de Estado para Serialización (Pickle/Multiprocessing).
        ---------------------------------------------------------------------
        Garantiza que el objeto sea serializable al eliminar la referencia al 
        pipeline de ML (que puede contener descriptores de archivos o estados 
        de memoria no serializables) durante el guardado de estado del agente.
        """
        state = self.__dict__.copy()
        state["_pipeline"] = None
        return state

# =============================================================================
# SECCIÓN 7 – AGENTE ORQUESTADOR
# =============================================================================

class OrquestadorAgente:
    """
    Controlador basado en Agentes Autónomos.
    -------------------------------------------------------------------------
    Esta clase implementa el patrón de diseño 'Agent-Tool-Interface', actuando 
    como el cerebro que coordina la lógica de negocio y la inferencia de ML.

    1. Abstracción del Modelo (LLM): Utiliza 'HfApiModel' para interactuar con 
        modelos de lenguaje de última generación (SOTA) a través del hub de 
        Hugging Face, permitiendo la intercambiabilidad de modelos.
    2. Framework smolagents: Implementa un 'ToolCallingAgent', una arquitectura 
        especializada en la generación de llamadas a funciones (Function Calling). 
        El agente no solo clasifica, sino que genera un plan de acción basado 
        en la consulta del usuario.
    3. Configuración de Hiperparámetros de Razonamiento:
        - 'max_steps': Controla el límite de iteraciones del ciclo ReAct para 
            evitar bucles infinitos de razonamiento y optimizar el coste de inferencia.
        - 'system_prompt': Inyecta las directrices de comportamiento y las 
            restricciones de seguridad de alto nivel (Metaprompting).
    """

    def __init__(
        self,
        pipeline_path: str,
        model_id: str = settings.MODELO,
        max_steps: int = 6,
        validator=None
    ):
        # Validación de credenciales para el acceso a la API de inferencia.
        token = settings.API_KEY
        if not token:
            raise ValueError("Configuración Crítica: HF_TOKEN no detectado.")

        self.model = HfApiModel(model_id=model_id, token=token)
        # Registro de la herramienta de ML desarrollada en la Sección 6.
        self.tools = [FraudDetectionTool(pipeline_path=pipeline_path)]
        self.validator = validator

        # Inicialización del Agente con capacidades de invocación de herramientas.
        self.agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
            system_prompt=settings.PROMPT,
            max_steps=max_steps,
        )

    def ejecutar_tarea(self, query: str) -> str:
        """
        Ciclo de Vida de Ejecución del Agente.
        ---------------------------------------------------------------------
        1. Ingesta: Recibe la consulta en lenguaje natural (ej: "Analiza este anuncio").
        2. Razonamiento: El LLM evalúa si necesita usar la 'FraudDetectionTool'.
        3. Acción: Ejecuta la herramienta de ML y recibe el JSON de resultados.
        4. Validación Post-Inferencia: Si existe un validador externo, se verifica 
            la consistencia de la respuesta final antes de entregarla al usuario, 
            añadiendo una capa de fiabilidad (Guardrailing).
        """
        resultado = self.agent.run(query)
        
        # Implementación de lógica de validación de salida para mitigar alucinaciones.
        if self.validator and not self.validator(resultado):
            return "Error de Consistencia: El resultado no superó los tests de validación."
            
        return resultado