from fastapi import APIRouter, Depends, UploadFile, File
import os
import sys
# --- Ajuste de path para poder ejecutar tanto script como uvicorn (inamovible de esta posición) ---
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_path not in sys.path:
    sys.path.append(root_path)
    
from api.models.schemas import AnuncioEntrada, TipoEntrada, ResultadoAnalisis, NivelSeguridad #from api.models.schemas import AnuncioEntrada, TipoEntrada, ResultadoAnalisis, NivelSeguridad
from servicios.traduccion_service import traducir_contenido       #from servicios.traduccion_service import traducir_contenido 

router = APIRouter()

@router.post("/analizar", response_model=ResultadoAnalisis)
async def analizar_anuncio(anuncio: AnuncioEntrada = Depends(AnuncioEntrada.as_form), file: UploadFile = File(None)):

    # Aquí se implementaría la lógica de análisis del anuncio
    # Por ahora, se devuelve un resultado simulado
    original, translated, idioma_detectado = await traducir_contenido(target_lang=anuncio.idioma_destino,file=file,text=anuncio.texto,url=anuncio.url)

    if idioma_detectado != "es":
        return ResultadoAnalisis(
            tipo_entrada=anuncio.tipo,
            nivel_seguridad=NivelSeguridad.ROJO,
            confianza_seguridad=0.0,
            mensaje="",
            indicadores=[""],
            idioma_detectado=idioma_detectado
        )
    
    # Simulación de preprocesado segun tipo de entrada
    if anuncio.tipo == TipoEntrada.IMAGEN:
        texto_limpio = "Texto extraído de la imagen (simulado)"
    elif anuncio.tipo == TipoEntrada.ENLACE:
        texto_limpio = "Texto extraído del enlace (simulado)"
    else:
        texto_limpio = "Texto limpio del anuncio (simulado)"


        # Aquí se podría agregar lógica específica para analizar texto
        # Futuro: resultado = ia_service.analizar_texto(texto_limpio)
    resultado = ResultadoAnalisis(
        tipo_entrada=anuncio.tipo,
        nivel_seguridad=NivelSeguridad.AMARILLO,
        confianza_seguridad=0.75,
        mensaje="",
        indicadores=["Uso de lenguaje ambiguo", "Falta de información clara"],
        idioma_detectado=idioma_detectado
        
    )
    return resultado


#Este archivo le corresponde al grupo de Backend, esto es solo un archivo de prueba
