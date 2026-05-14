# "El archivo traduccion.py se encarga de gestionar la traducción y detección de un texto
# (en formato string, url o imagen) en español. Es uno de los tres archivos encargados
# para conectar el Backend con el Frontend mediante un APIRouter"

# "Librerías y funciones que gestionan la lógica de traducción, principalmente a través de traduccion_service.py"
from fastapi import APIRouter, Depends, UploadFile, File
import os
import sys

# "Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición)"
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

from api.models.schemas import TextoDetectar, ResultadoDeteccion        
from servicios.traduccion_service import traducir_contenido       

router = APIRouter()

# "Función que define una ruta POST en FastAPI para detectar y traducir el idioma de un texto
# y opcionalmente un archivo subido por el usuario usando las clases definidas para ello."
@router.post("/detectar_idioma", response_model=ResultadoDeteccion)
async def detectar_idioma(texto: TextoDetectar = Depends(TextoDetectar.as_form), file: UploadFile = File(None)):
    
    # "Extrae contenido y detecta idioma usando la función de traduccion_service.py"
    original, translated, idioma_detectado = await traducir_contenido(
        target_lang=texto.idioma_destino,
        file=file,
        text=texto.texto,
        url=texto.url
    )

    # "Verificar que el idioma detectado es español para devolver el resultado de la detección/traducción"
    if idioma_detectado != "es":
        return ResultadoDeteccion(
            idioma_detectado=idioma_detectado,
            es_analizable=False,
            mensaje="",
            original=original,
            traducido=""
        )
        
    resultado = ResultadoDeteccion(
        idioma_detectado=idioma_detectado,
        es_analizable=True,
        mensaje="",
        original=original,
        traducido=translated
    )

    return resultado
