from fastapi import FastAPI
import logging

from src.interfaces.controllers import scans
from src.domain.exceptions import BusinessException
from src.infrastructure.handlers.exception_handler import business_exception_handler

# Inicializa la aplicaci�n FastAPI con t�tulo y versi�n
app = FastAPI(
    root_path="/security",
    title="Security Scan",
    version="1.0",
    description=(
        "API RESTful para escaner de vulnerabilidades de un swagger."
    ),
    contact={
        "name": "Santiago Zapata Alvarez",
        "email": "zapataalva4@gmail.com",
    },
)

# Registro de rutas (endpoints definidos en otros m�dulos)
app.include_router(scans.router)      # Rutas relacionadas con escaneo front-end

# Configuraci�n b�sica de logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Formato de salida
)

# Registro de un handler global para excepciones de tipo BusinessException
app.add_exception_handler(BusinessException, business_exception_handler)

# Endpoint simple de salud (para verificar si la API est� activa)
@app.get("/health")
def health_check():
    return {"status": "ok"}

