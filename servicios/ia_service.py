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

import json
import logging
import re
import unicodedata
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from smolagents import LiteLLMModel, Tool, ToolCallingAgent

from api.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# SECCIÓN 1 – CONSTANTES Y REGEX DE SEGURIDAD
# =============================================================================

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
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|" r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064]"
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
        raise ValueError(
            f"'{field_name}' contiene caracteres de control no permitidos."
        )
    if CODE_INJECTION_RE.search(value):
        raise ValueError(f"'{field_name}' contiene código HTML/SQL malicioso.")
    if PROMPT_INJECTION_RE.search(value):
        raise ValueError(f"'{field_name}' contiene instrucciones de inyección de IA.")

    return value


def _check_byte_size(value: str, max_bytes: int, field_name: str) -> str:
    """
    Verifica que el campo no supere el límite de bytes en UTF-8.

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
    """

    descripcion: Optional[str] = Field(default=None, max_length=3000)
    url_oferta: Optional[str] = Field(default=None, max_length=300)

    # Captura cualquier campo extra que venga en el anuncio

    @field_validator("descripcion", mode="before")
    @classmethod
    def sanitize_descripcion(cls, v, info):
        if v is None:
            return v
        return _sanitize(str(v), field_name=info.field_name)

    @field_validator("descripcion", mode="after")
    @classmethod
    def descripcion_byte_limit(cls, v):
        if v is None:
            return v
        return _check_byte_size(v, MAX_BYTES_DESCRIPCION, "descripcion")


# =============================================================================
# SECCIÓN 5 – ORQUESTADOR DE VALIDACIÓN
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
    ad = JobAdInput(**data)
    return ad.model_dump()


# =============================================================================
# SECCIÓN 7 – TOOL DE DETECCIÓN ML
# =============================================================================


# Jerarquía de Relevancia Semántica
# -----------------------------------------------------------------------------
# Se establece un orden determinista de campos basado en su peso estadístico
# para la detección de fraude.
def _generar_justificacion(label: int, proba: float, senales: list) -> str:
    pct = round(proba * 100)
    if label == 1:
        base = f"El modelo detecta un riesgo de fraude del {pct}%."
        if senales:
            senales_formateadas = [str(s) for s in senales[:4]]
            base += (
                f" Señales de alerta identificadas: {', '.join(senales_formateadas)}."
            )
    else:
        base = f"El modelo no detecta señales significativas de fraude (probabilidad estimada: {pct}%)."
    return base


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

    name = "fraud_detection"
    description = (
        "Detects fraud in job postings. "
        "Analyzes text signals, linguistic patterns, and ML predictions. "
        "Input can be a JSON string or object with job posting fields (descripcion, titulo, empresa, etc.). "
        "Returns JSON with verdict (FRAUDULENT/LEGITIMATE), probability, confidence, signals, and reasoning."
    )

    inputs = {
        "job_posting_json": {
            "type": "string",
            "description": "Job posting data as JSON string or object. Can include: descripcion, titulo, empresa, salario_min, salario_max, url_oferta, etc.",
        }
    }
    output_type = "string"

    _CONFIDENCE_MAP = [
        (0.75, "high"),
        (0.55, "medium"),
        (0.0, "low"),
    ]

    def __init__(self, pipeline_path: str, **kwargs):
        super().__init__(**kwargs)
        self._pipeline_path = pipeline_path
        self._pipeline = None  # lazy loading

    def _load_pipeline(self) -> None:
        """
        Carga el pipeline de ML en memoria solo una vez.

        Esta función usa lazy loading para retrasar la carga del modelo hasta que
        se necesita la primera inferencia.
        """
        if self._pipeline is None:
            import joblib

            data = joblib.load(self._pipeline_path)
            model = data["model"]
            model.set_params(device="cpu")
            self._pipeline = {
                "model": model,
                "threshold": data["threshold"],
                "sbert_model_name": data["sbert_model_name"],
                "encoder": None,
            }

    def _get_encoder(self) -> object:
        """
        Obtiene el encoder SBERT del pipeline, cargándolo si es necesario.
        """
        if self._pipeline["encoder"] is None:
            from sentence_transformers import SentenceTransformer

            self._pipeline["encoder"] = SentenceTransformer(
                self._pipeline["sbert_model_name"], device="cpu"
            )
        return self._pipeline["encoder"]

    def _get_confidence_level(self, probability: float) -> str:
        """
        Traduce una probabilidad continua en un nivel de confianza discreto.
        """
        for threshold, level in self._CONFIDENCE_MAP:
            if probability >= threshold:
                return level
        return "low"

    async def forward(self, job_posting_json: str) -> str:
        """
        Ejecuta la herramienta de detección de fraude sobre un anuncio JSON.

        Espera un JSON serializado con campo `resultado_procesado` y devuelve
        un JSON serializado con veredicto, probabilidad y metadatos.
        """

        # 1. Deserializar
        try:
            fields = json.loads(job_posting_json)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.error(f"Error al deserializar entrada: {exc}")
            return json.dumps(
                {"error": f"Formato de entrada inválido: {exc}"}, ensure_ascii=False
            )

        # 2. Usar resultado ya procesado
        resultado_proc = fields.get("resultado_procesado")
        if not resultado_proc:
            return json.dumps(
                {"error": "No se recibió resultado procesado."}, ensure_ascii=False
            )

        # 3. Predicción ML
        try:
            texto_para_modelo = resultado_proc.get("texto_normalizado", "")
            if not texto_para_modelo:
                return json.dumps(
                    {"error": "Texto inválido para procesamiento"}, ensure_ascii=False
                )

            self._load_pipeline()

            encoder = self._get_encoder()
            embedding = encoder.encode([texto_para_modelo])
            logger.debug(f"Embedding generado, shape: {embedding.shape}")

            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)

            predicciones = self._pipeline["model"].predict_proba(embedding)
            logger.debug(f"Predicciones recibidas, shape: {predicciones.shape}")

            proba_fraud = float(predicciones[0, 1])
            logger.debug(f"Probabilidad extraída: {proba_fraud}")

            label = 1 if proba_fraud >= self._pipeline["threshold"] else 0

            # Procesar señales de forma segura
            try:
                senales = resultado_proc.get("senales", {})
                if isinstance(senales, dict):
                    senales_sin_fuente = {
                        k: v for k, v in senales.items() if k != "fuente"
                    }
                    raw_list = list(senales_sin_fuente.values())
                else:
                    raw_list = senales if isinstance(senales, list) else []

                # Aplanamos y limpiamos: extraemos el string si es ['texto'] y quitamos vacíos
                senales_list = []
                for s in raw_list:
                    if isinstance(s, list) and len(s) > 0:
                        item = str(s[0]).strip()
                    else:
                        item = str(s).strip()

                    if item and item not in ["[]", "None", ""]:
                        senales_list.append(item)

            except Exception as e:
                logger.warning(f"Error procesando señales: {e}")
                senales_list = []

            return json.dumps(
                {
                    "verdict": "FRAUDULENT" if label == 1 else "LEGITIMATE",
                    "probability": round(proba_fraud, 4),
                    "confidence_level": self._get_confidence_level(proba_fraud),
                    "fuente": resultado_proc.get("fuente", "desconocida"),
                    "senales": senales_list,
                    "caracteristicas": resultado_proc.get("caracteristicas", {}),
                    "estadisticas": resultado_proc.get("estadisticas", {}),
                    "justificacion": _generar_justificacion(
                        label, proba_fraud, senales_list
                    ),
                },
                ensure_ascii=False,
            )

        except Exception as e:
            logger.error(
                f"Error inesperado en forward(): {type(e).__name__}: {e}", exc_info=True
            )
            return json.dumps(
                {
                    "error": f"Error inesperado: {type(e).__name__}",
                    "verdict": None,
                    "probability": None,
                    "confidence_level": None,
                },
                ensure_ascii=False,
            )

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_pipeline"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


# =============================================================================
# SECCIÓN 8 – AGENTE ORQUESTADOR
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
        validator=None,
    ):
        self.model = LiteLLMModel(model_id="ollama/qwen2.5:3b")
        self.tools = [FraudDetectionTool(pipeline_path=pipeline_path)]
        self.validator = validator

        self.agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
            max_steps=max_steps,
        )
        self.agent.prompt_templates["system_prompt"] = (
            settings.PROMPT
            + "\n\nIMPORTANT: Always call the fraud_detection tool before providing any answer. "
            "Never respond directly with a JSON result without first calling the tool."
        )

    async def ejecutar_tarea(self, query: str) -> str:
        """
        Orquestación de Ejecución Híbrida (ML + Agente).

        Este método implementa un flujo de trabajo en dos etapas:
        1. Ejecución Técnica (Tool de ML): Se procesa la entrada del anuncio a través
        de la herramienta de detección de fraude, obteniendo un análisis técnico
        detallado en formato JSON.
        2. Ejecución Narrativa (Agente): Se le proporciona al agente tanto el resultado
        técnico como el contenido original del anuncio, y se le asigna la tarea de
        generar una explicación breve, clara y directa para el usuario final,
        enriqueciendo así la justificación genérica del modelo de ML con una
        narrativa más humana y contextualizada.
        3. Ensamblaje Final: Se integra la explicación generada por el agente en el
        JSON de salida, reemplazando la justificación técnica con una narrativa
        más rica y comprensible para el usuario.
        """
        try:
            # 1. Preparar la entrada
            if isinstance(query, str):
                try:
                    query_data = json.loads(query)
                except json.JSONDecodeError:
                    query_data = {"descripcion": query}
            else:
                query_data = query

            job_posting_json = json.dumps(query_data, ensure_ascii=False)

            # 2. EJECUCIÓN TÉCNICA (Tool de confianza)
            # Obtenemos los datos duros que el frontend necesita para el semáforo y gráficas
            logger.info("Obteniendo datos técnicos de la Tool...")
            tool_result_str = await self.tools[0].forward(
                job_posting_json=job_posting_json
            )
            datos_finales = json.loads(tool_result_str)

            if "error" in datos_finales:
                return tool_result_str

            # 3. EJECUCIÓN NARRATIVA (Agente)
            # Le pedimos que genere SOLO el mensaje para el usuario
            tarea = (
                f"Analiza este anuncio siguiendo tus instrucciones de experto.\n"
                f"DATOS TÉCNICOS: {tool_result_str}\n"
                f"CONTENIDO DEL ANUNCIO: {job_posting_json}\n"
                "TAREA: Escribe una explicación breve (2-3 frases) para el usuario. "
                "Usa un tono directo y neutral. No devuelvas JSON, solo el texto."
            )

            logger.info("Iniciando razonamiento narrativo del agente...")
            # Aquí capturamos la respuesta del agente como un string simple
            import litellm

            respuesta = litellm.completion(
                model="ollama/qwen2.5:3b", messages=[{"role": "user", "content": tarea}]
            )
            mensaje_agente = respuesta.choices[0].message.content.strip()

            # 4. ENSAMBLAJE FINAL
            # Sustituimos la justificación genérica de la tool por la narrativa rica del agente
            if mensaje_agente and len(mensaje_agente) > 10:
                # Limpiamos posibles artefactos por si el agente escribe "Respuesta: ..."
                mensaje_limpio = re.sub(
                    r"^(Respuesta|Justificación|Mensaje):\s*",
                    "",
                    mensaje_agente,
                    flags=re.IGNORECASE,
                )
                datos_finales["justificacion"] = mensaje_limpio

            # Devolvemos el JSON de la Tool enriquecido con el texto del Agente
            return json.dumps(datos_finales, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error crítico en ejecutar_tarea: {e}", exc_info=True)
            # Si todo falla, al menos devolvemos algo que el frontend entienda
            return json.dumps(
                {
                    "error": "Error en el análisis",
                    "verdict": "AMBIGUO",
                    "probability": 0.0,
                    "confidence_level": "low",
                    "justificacion": "No se pudo completar el análisis técnico.",
                },
                ensure_ascii=False,
            )
