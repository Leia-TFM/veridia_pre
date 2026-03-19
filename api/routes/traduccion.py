from fastapi import APIRouter, Depends, UploadFile, File
import os
import sys
# --- Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición) ---
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)

from api.models.schemas import TextoDetectar, ResultadoDeteccion        #Entrega final:  from api.models.schemas import TextoDetectar, ResultadoDeteccion
from servicios.traduccion_service import traducir_contenido       #from servicios.traduccion_service import traducir_contenido 

router = APIRouter()

@router.post("/detectar_idioma", response_model=ResultadoDeteccion)
async def detectar_idioma(texto: TextoDetectar = Depends(TextoDetectar.as_form), file: UploadFile = File(None)):
    
    # Aquí se implementaría la lógica de detección de idioma
    original, translated, idioma_detectado = await traducir_contenido(target_lang=texto.idioma_destino,file=file,text=texto.texto,url=texto.url)

     # comprobador de idioma en el router
    if idioma_detectado != "es":
        return ResultadoDeteccion(
            idioma_detectado=idioma_detectado,
            es_analizable=False,
            mensaje=f"Idioma no soportado. El idioma detectado es ({idioma_detectado}). Solo se admite español (es).",
            original=original,
            traducido=""
        )
        
    resultado = ResultadoDeteccion(
        idioma_detectado=idioma_detectado,
        es_analizable=True,
        mensaje="El texto es en español (es) y es analizable.",
        original=original,
        traducido=translated
    )

    return resultado

#PASO 1: COMANDO CON EL REQUIREMENTS
#requirements:  pip install -r requirements.txt

# Ejecución: uvicorn api.routes.traduccion:app --reload + en otra terminal el streamlit de app.py
# Ejecución (local): uvicorn traduccion:app --reload + en otra terminal el streamlit de app.py