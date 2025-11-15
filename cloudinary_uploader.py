# ==========================================================================
# ARCHIVO cloudinary_uploader.py
# ==========================================================================
import cloudinary
import cloudinary.uploader
import io

# ==========================================================================
# CONFIGURACIÓN INICIAL
# Pega aquí las credenciales que obtuviste de tu Dashboard de Cloudinary.
# ==========================================================================
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env que acabas de crear
load_dotenv()

# CONFIGURACIÓN INICIAL (AHORA SEGURA)
# Lee las credenciales desde las variables de entorno
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)


def subir_a_cloudinary(buffer_imagen: io.BytesIO, nombre_archivo: str) -> str:
    """
    Sube un archivo en memoria (buffer) a Cloudinary y devuelve la URL pública.
    """
    try:
        # Extraemos el nombre sin la extensión para usarlo como public_id
        # Ejemplo: "entrada-123.png" -> "entrada-123"
        public_id = nombre_archivo.rsplit('.', 1)[0]

        # Usamos la función de subida de Cloudinary
        # Le pasamos el buffer, un ID público y le decimos que sobreescriba si ya existe
        upload_result = cloudinary.uploader.upload(
            buffer_imagen, 
            public_id=public_id,
            overwrite=True
        )

        # El resultado es un diccionario, la URL está en la clave 'secure_url'
        print(f"\n[CLOUDINARY] Imagen subida con éxito. URL: {upload_result['secure_url']}\n")
        return upload_result['secure_url']

    except Exception as e:
        print(f"\n[ERROR EN CLOUDINARY] No se pudo subir el archivo: {e}\n")
        raise e