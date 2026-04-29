import pytesseract
from PIL import Image
import cv2 
import numpy as np 

# CARGAR IMAGEN
def cargar_imagen(file_bytes):
    np_arr = np.frombuffer(file_bytes, np.uint8)
    imagen = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError(
            "FORMATO_NO_VÁLIDO",
            "El formato no compatible."
        )
    return imagen


# FILTROS
## Escala de grises
def escala_grises(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY) 
    return gris

## Reescalar
def escalar_imagen(imagen, min_size=1200):
    h, w = imagen.shape[:2] 
    if max(h, w) < 200: 
        raise ValueError(
            "IMÁGEN_DEMASIADO_PEQUEÑA",
            "La imágen es demasiado pequeña para procesarla."
        )

    if max(h, w) < min_size:
        scale = 2 if max(h, w) * 2 >= min_size else 3   # Calculamos si con x2 basta o si necesitamos x3 para llegar al min_size
        imagen = cv2.resize(
            imagen,
            None,
            fx=scale, 
            fy=scale, 
            interpolation=cv2.INTER_CUBIC 
        )
    return imagen

## Filtro de nitidez
def aumentar_nitidez(imagen):
    return cv2.bilateralFilter(imagen, 9, 75, 75) # Quita ruido de fondo

## Contraste en base al color de fondo: no sabe leer blanco sobre negro
def subir_contraste(imagen):
    h, w = imagen.shape[:2]
    roi = imagen[h//4:3*h//4, w//4:3*w//4] # Toma muestra del centro de la imagen e ignora los bordes para saber cómo es el fondo
    if np.median(roi) < 120:
        imagen = cv2.bitwise_not(imagen) # Invierte los colores
    return imagen

## Binarización
def binarizar(imagen):
    thresh = cv2.adaptiveThreshold(
        imagen, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 61, 25 
    )
    
    # Eliminar manchas que puedan generar ruido
    dist = cv2.bitwise_not(thresh)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(dist, connectivity=8)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] < 10:
            thresh[labels == i] = 255
            
    # Marco blanco para que Tesseract no corte texto
    thresh = cv2.copyMakeBorder(thresh, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=255)
    return thresh

## Ordenar los puntos de perspectiva para mappear la imagen
def ordenar_puntos(pts):
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]    # arriba-izquierda
    rect[2] = pts[np.argmax(s)]    # abajo-derecha
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # arriba-derecha
    rect[3] = pts[np.argmax(diff)] # abajo-izquierda
    
    return rect   

## Perspectiva deskewing para imagenes en ángulo
def corregir_perspectiva(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
    _, thresh = cv2.threshold(desenfoque, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contornos: 
        return imagen
    
    contorno_largo = max(contornos, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(contorno_largo, True)
    aprox = cv2.approxPolyDP(contorno_largo, epsilon, True)
    
    # si detecta 4 puntos, corrige perspectiva
    if len(aprox) == 4:
        pts = aprox.reshape(4, 2)
        rect = ordenar_puntos(pts)
        (tl, tr, br, bl) = rect 
        
        anchoA = np.linalg.norm(br - bl)
        anchoB = np.linalg.norm(tr - tl)
        maxAncho = max(int(anchoA), int(anchoB))
        
        alturaA = np.linalg.norm(tr - br)
        alturaB = np.linalg.norm(tl - bl)
        maxAltura = max(int(alturaA), int(alturaB))
        
        # definir puntos para transformar la perspectiva
        dst = np.array([
            [0, 0],                          
            [maxAncho - 1, 0],               
            [maxAncho - 1, maxAltura - 1],   
            [0, maxAltura - 1]              
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(imagen, M, (maxAncho, maxAltura))
            
    return imagen

# PREPROCESADO
def preprocesar_imagen(file_bytes):
    try:
        imagen = cargar_imagen(file_bytes)
        imagen = corregir_perspectiva(imagen)
        imagen = escala_grises(imagen)
        imagen = escalar_imagen(imagen)
        imagen = aumentar_nitidez(imagen)    
        imagen = subir_contraste(imagen) 
        imagen = binarizar(imagen) 
        
        return {'status': 'success', 
                'image': imagen}
     
    except ValueError as e: 
        if len(e.args) == 2:
            return {
                'status': 'error',
                'text': 'Not Found',
                'error_txt': e.args[0], 
                'error_msg': e.args[1] 
            }
        else:
            return {
                'status': 'error',
                'text': 'Not Found',
                'error_txt': 'ERROR_INESPERADO',
                'error_msg': str(e)
            }

# MOTOR
def motor(imagen, idioma="spa"):
    # --psm 3 es el modo de segmentación predeterinado
    # --oem 3 es el motor de OCR LSTM más avanzado
    # preserve_interword_spaces=1 es para mantener los espacios entre palabras
    config_tesseract = "--psm 3 --oem 3 -c preserve_interword_spaces=1" 
    texto = pytesseract.image_to_string(imagen, lang=idioma, config=config_tesseract)
    return texto.strip()  


# FUNCIÓN PRINCIPAL
def extraer_texto(file_bytes: bytes) -> dict:
    resultado = preprocesar_imagen(file_bytes)
    if resultado['status'] == 'error':
        return resultado
        
    imagen_pil = Image.fromarray(resultado['image'])
    texto = motor(imagen_pil)
    
    return {'status': 'success', 
            'text': texto}