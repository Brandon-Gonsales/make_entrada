# Etapa 1: Base de Python
FROM python:3.9-slim

# Etapa 2: Establecer directorio de trabajo
WORKDIR /app

# Etapa 3: Instalar dependencias de Python
# Copiamos SOLO el archivo de requerimientos primero para aprovechar el cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 4: Copiar la carpeta de assets explícitamente
# Este comando copia la carpeta 'assets' de tu PC a una carpeta 'assets' dentro de /app
COPY assets ./assets

# Etapa 5: Copiar el resto del código de la aplicación
COPY main.py .

# ---- PASO DE DEPURACIÓN ----
# Este comando nos mostrará en la consola de build exactamente qué archivos hay en /app
# Busca su salida cuando ejecutes 'docker build'
RUN ls -R

# Etapa 6: Exponer puerto y ejecutar
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]