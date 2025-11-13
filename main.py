# ==========================================================================
# ARCHIVO main.py - PRUEBA DE DIAGNÓSTICO FINAL (POSICIÓN 0, 0)
# ==========================================================================
import os
import io
import qrcode
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# INICIALIZACIÓN DE LA APP
# --------------------------------------------------------------------------
app = FastAPI(
    title="API Generadora de Entradas con Plantilla",
    description="Una API para crear imágenes de entradas usando la librería Pillow.",
    version="7.1.1 (Corrección QR)"
)

# --------------------------------------------------------------------------
# MODELO DE DATOS
# --------------------------------------------------------------------------
class EntradaRequest(BaseModel):
    nombre: str = Field(..., example="Mariana Castillo")
    monto_pagado: str = Field(..., example="Bs. 100")
    metodo_pago: str = Field(..., example="QR Simple")
    datos_qr: str = Field(..., example="GARGOLA-2025-TICKET-D4E5F6")

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
