# app.py

# --- Sección 1: Importación de Librerías ---
# Estas son las herramientas que necesitamos para que el programa funcione.

import os  # Para interactuar con el sistema operativo, en este caso, para construir rutas de archivos.
import cv2  # OpenCV: La librería principal para todo el procesamiento y análisis de imágenes.
import numpy as np  # NumPy: Se usa para manejar las imágenes como matrices de números, que es como OpenCV las procesa.
from PIL import Image  # Pillow (PIL): Otra librería para trabajar con imágenes, útil para abrir los archivos que sube el usuario.
import io  # Para manejar los datos de la imagen en memoria, sin necesidad de guardarlos en un archivo.
import base64  # Para convertir la imagen final a un texto (en formato Base64) y poder enviarla al navegador.
from flask import Flask, request, jsonify, render_template  # Flask: Es el micro-framework que nos permite crear el servidor web (el backend).
from flask_cors import CORS  # Flask-CORS: Una extensión de Flask para permitir que tu frontend (en otra "dirección") se comunique con este backend.


# --- Sección 2: Configuración de la Aplicación Flask ---
# Aquí preparamos nuestro servidor web.

# Se crea la ruta absoluta a la carpeta 'Frontend'.
# os.path.dirname(__file__) -> Obtiene la carpeta actual ('Backend').
# '..' -> Sube un nivel (a 'Analizador').
# 'Frontend' -> Entra a la carpeta Frontend.
# El resultado es la ruta completa a 'D:\Proyectos JAN\Analizador\Frontend'.
frontend_folder = os.path.join(os.path.dirname(__file__), '..', 'Frontend')

# Se inicializa la aplicación Flask.
# Le decimos explícitamente dónde buscar los archivos HTML (template_folder) y los archivos CSS/JS (static_folder).
app = Flask(__name__, 
            template_folder=frontend_folder, 
            static_folder=frontend_folder)

# Se habilita CORS para la aplicación, permitiendo las peticiones desde el frontend.
CORS(app)


# --- Sección 3: Rutas del Servidor (Endpoints) ---
# Estas son las "direcciones" o URLs que el navegador puede visitar.

@app.route('/')
def index():
    """
    Esta función se ejecuta cuando alguien visita la página principal (ej. http://127.0.0.1:5000/).
    Devuelve el archivo 'index.html' para que el navegador lo muestre.
    """
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def handle_analyze():
    """
    Este es el endpoint principal de nuestra API. Se activa cuando el JavaScript le envía una imagen.
    Solo acepta peticiones de tipo POST (envío de datos).
    """
    # 1. Verificación: Nos aseguramos de que el usuario realmente envió un archivo.
    if 'image' not in request.files:
        return jsonify({"error": "Se requiere un archivo de imagen."}), 400

    file = request.files['image']

    # 2. Procesamiento del archivo: Abrimos el archivo de imagen enviado.
    try:
        # Usamos Pillow para abrir el archivo directamente desde la memoria.
        img_pil = Image.open(file.stream)
    except Exception as e:
        # Si el archivo no es una imagen válida, devolvemos un error.
        return jsonify({"error": f"No se pudo procesar el archivo: {e}"}), 400

    # 3. Análisis de la imagen: Llamamos a nuestra función principal de procesamiento.
    analysis_image = analyze_surface(img_pil)

    # 4. Conversión del resultado: Convertimos la imagen resultante a formato Base64.
    analysis_image_url = image_to_base64_data_url(analysis_image)

    # 5. Envío de la respuesta: Devolvemos un objeto JSON al JavaScript con la URL de la imagen analizada.
    return jsonify({
        "analysis_image_url": analysis_image_url
    })


# --- Sección 4: Lógica de Procesamiento de Imagen ---
# Aquí ocurre la "magia" del análisis de superficie.

def analyze_surface(img_pil):
    """
    Analiza la superficie de una imagen para resaltar imperfecciones.
    Recibe: una imagen en formato Pillow.
    Devuelve: una imagen en formato Pillow con el análisis visual.
    """
    # Paso A: Convertir la imagen de formato Pillow a formato OpenCV (matriz NumPy).
    img_cv = np.array(img_pil.convert('RGB'))
    
    # Paso B: Convertir la imagen a escala de grises. El análisis de formas y texturas es más simple y efectivo sin color.
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Paso C: Aplicar un desenfoque Gaussiano. Esto suaviza la imagen para eliminar el "ruido"
    # (pequeños detalles de la textura que no son imperfecciones) y evitar falsos positivos.
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Paso D: Usar transformaciones morfológicas para encontrar las anomalías.
    # Un "kernel" es una pequeña matriz que se desliza sobre la imagen para analizar vecindarios de píxeles.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    
    # "Black-hat" encuentra puntos oscuros (fisuras, huecos, poros) que son más pequeños que el kernel.
    blackhat = cv2.morphologyEx(blurred, cv2.MORPH_BLACKHAT, kernel)
    
    # "Top-hat" encuentra puntos brillantes (bultos, hilos, gotas de material) que son más pequeños que el kernel.
    tophat = cv2.morphologyEx(blurred, cv2.MORPH_TOPHAT, kernel)

    # Sumamos los dos mapas para tener una imagen que contiene tanto los defectos oscuros como los brillantes.
    imperfections_map = cv2.add(blackhat, tophat)

    # Paso E: Crear un "mapa de calor" (heatmap) a partir del mapa de imperfecciones.
    # Esto asigna un color a cada nivel de intensidad. Los píxeles más blancos (mayor imperfección)
    # se volverán rojos/amarillos, y los negros (sin imperfección) se volverán azules.
    heatmap = cv2.applyColorMap(imperfections_map, cv2.COLORMAP_JET)

    # Paso F: Superponer el mapa de calor sobre la imagen original.
    # Esto crea un efecto semitransparente que nos permite ver las imperfecciones
    # coloreadas directamente sobre la pieza original, facilitando su localización.
    alpha = 0.5  # Nivel de transparencia (0.5 = 50%).
    superimposed_img = cv2.addWeighted(heatmap, alpha, img_cv, 1 - alpha, 0)

    # Paso G: Convertir la imagen final de vuelta a formato Pillow para poder guardarla en memoria.
    return Image.fromarray(superimposed_img)


def image_to_base64_data_url(img, format="PNG"):
    """
    Función auxiliar para convertir un objeto de imagen de Pillow a una cadena de texto Base64.
    El navegador puede interpretar esta cadena de texto directamente y mostrarla como una imagen.
    """
    buffered = io.BytesIO()  # Crea un archivo binario en memoria.
    img.save(buffered, format=format)  # Guarda la imagen en ese archivo en memoria.
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")  # Codifica los datos binarios a texto.
    return f"data:image/{format.lower()};base64,{img_str}"  # Devuelve la cadena con el formato correcto de Data URL.


# --- Sección 5: Punto de Entrada de la Aplicación ---
# Esta es la parte que ejecuta el servidor cuando corres "python app.py" en la terminal.

# if __name__ == '__main__':
    """
    La condición __name__ == '__main__' es estándar en Python.
    Asegura que el código dentro de ella solo se ejecute cuando el script es el archivo principal,
    y no cuando es importado por otro script.
    """
    # app.run() inicia el servidor web de Flask.
    # debug=True activa el modo de depuración, que reinicia el servidor automáticamente cuando haces cambios en el código.
    # port=5000 especifica el puerto en el que se ejecutará el servidor.
    # app.run(debug=True, port=5000)