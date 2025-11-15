# ==========================================================================
# ARCHIVO main.py - PRUEBA DE DIAGNÓSTICO FINAL (POSICIÓN 0, 0)
# ==========================================================================
import os
import io
import qrcode
from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont

from cloudinary_uploader import subir_a_cloudinary
# --------------------------------------------------------------------------
# INICIALIZACIÓN DE LA APP
# --------------------------------------------------------------------------
app = FastAPI(
    title="API Generadora y de Subida de Entradas (con Cloudinary)",
    description="Una API con dos endpoints: uno para crear la imagen y otro para subirla a Cloudinary.",
    version="10.0.0 (Migración a Cloudinary)"
)

# --------------------------------------------------------------------------
# MODELO DE DATOS
# --------------------------------------------------------------------------
class EntradaRequest(BaseModel):
    id_entrada: str = Field(..., example="#00001-A8B2")
    nombre: str = Field(..., example="Mariana Castillo")
    monto_pagado: str = Field(..., example="Bs. 100")
    metodo_pago: str = Field(..., example="QR Simple")
    datos_qr: str = Field(..., example="GARGOLA-2025-TICKET-D4E5F6")

class UploadResponse(BaseModel):
    url: str = Field(..., example="https://res.cloudinary.com/...") # Cambiado a 'url' genérico
    filename: str = Field(..., example="entrada-A8B2.png")
# --------------------------------------------------------------------------
# LÓGICA DE GENERACIÓN DE IMAGEN
# --------------------------------------------------------------------------
def crear_imagen_con_plantilla(data: EntradaRequest) -> io.BytesIO:
    """
    Abre una plantilla, genera un QR, y escribe texto sobre la imagen.
    """
    try:
        # --- 1. Carga de recursos ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_plantilla = os.path.join(script_dir, "assets", "template.png")
        ruta_font_bold = os.path.join(script_dir, "assets", "fonts", "Roboto-Bold.ttf")
        ruta_font_regular = os.path.join(script_dir, "assets", "fonts", "Roboto-Regular.ttf")

        plantilla = Image.open(ruta_plantilla).convert("RGBA")
        draw = ImageDraw.Draw(plantilla)

        # --- 2. Escritura de texto ---
        font_valor_nombre = ImageFont.truetype(ruta_font_bold, 30)
        font_valor_regular = ImageFont.truetype(ruta_font_regular, 30)
        color_texto = "#212121"
        draw.text((437, 490), data.nombre, font=font_valor_nombre, fill=color_texto)
        draw.text((437, 540), data.monto_pagado, font=font_valor_regular, fill=color_texto)
        draw.text((437, 590), data.metodo_pago, font=font_valor_regular, fill=color_texto)
        # ==================================================================
        # INICIO DEL CÓDIGO AÑADIDO PARA EL ID
        # ==================================================================
        # --- 2.5. Escritura del ID en la esquina inferior derecha ---
        font_id = ImageFont.truetype(ruta_font_regular, 24)
        color_id = "#616161"  # Un color gris para que no sea tan prominente
        texto_id = data.id_entrada

        # Medimos el tamaño del texto para saber dónde posicionarlo
        ancho_plantilla, alto_plantilla = plantilla.size
        bbox_id = draw.textbbox((0, 0), texto_id, font=font_id)
        ancho_texto_id = bbox_id[2] - bbox_id[0]

        # Definimos un margen para que no quede pegado a los bordes
        margen_derecho = 40
        margen_inferior = 5

        # Calculamos la posición (x, y) de la esquina superior izquierda del texto
        posicion_id = (
            ancho_plantilla - ancho_texto_id - margen_derecho,
            alto_plantilla - bbox_id[3] - margen_inferior
        )
        
        # Finalmente, dibujamos el texto en la imagen
        draw.text(posicion_id, texto_id, font=font_id, fill=color_id)
        # ==================================================================
        # FIN DEL CÓDIGO AÑADIDO
        # ==================================================================
        # --- 3. Generación de QR ---
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=2
        )
        qr.add_data(data.datos_qr)
        qr.make(fit=True)

        # Convertimos a RGBA para compatibilidad con la plantilla
        qr_img_original = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

        # --- 4. PRUEBA DE DIAGNÓSTICO: Forzar posición a (0, 0) ---
        ancho_plantilla, alto_plantilla = plantilla.size
        ancho_qr, alto_qr = qr_img_original.size
        x_qr = ((ancho_plantilla-1313-ancho_qr)// 2)+1313  # posición fija desde donde comienza el QR
        y_qr = (alto_plantilla - alto_qr) // 2  # centrado verticalmente
        posicion_qr = (x_qr, y_qr)
        print(f"\n[DIAGNÓSTICO] Posición del QR: {posicion_qr} (x desde 1312, y centrado)\n")

        # --- 5. Pegado final (ahora seguro) ---
        plantilla.paste(qr_img_original, posicion_qr, mask=qr_img_original)

        # --- 6. Guardado en memoria ---
        buffer = io.BytesIO()
        plantilla.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer

    except Exception as e:
        print(f"\n[FATAL ERROR] Ha ocurrido una excepción: {e}\n")
        raise e

# --------------------------------------------------------------------------
# ENDPOINT
# --------------------------------------------------------------------------
@app.post("/generar-entrada")
async def endpoint_generar_entrada(datos_entrada: EntradaRequest = Body(...)):
    """
    Recibe los datos del asistente y genera una imagen PNG de la entrada.
    """
    try:
        buffer_imagen = crear_imagen_con_plantilla(datos_entrada)
        return StreamingResponse(buffer_imagen, media_type="image/png")
    except Exception as e:
        print(f"Error inesperado en el endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")

@app.post("/subir-imagen", response_model=UploadResponse) # Renombré la ruta para más claridad
async def endpoint_subir_imagen(file: UploadFile = File(...)):
    """
    Recibe un archivo de imagen, lo sube a Cloudinary y devuelve la URL pública.
    """
    try:
        contenido_imagen = await file.read()
        buffer_para_subir = io.BytesIO(contenido_imagen)
        
        # --- ¡ESTE ES EL ÚNICO CAMBIO LÓGICO! ---
        # Llamamos a la nueva función de Cloudinary
        url_publica = subir_a_cloudinary(buffer_para_subir, file.filename)
        
        return {"url": url_publica, "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado al subir: {e}")