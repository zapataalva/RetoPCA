# DAST Scanner (FastAPI + Clean Architecture)

Servicio sincronico que recibe un archivo OpenAPI/Swagger en JSON, ejecuta el escaneo DAST y guarda resultados en MongoDB.

## Estructura
- `src/domain`: entidades de dominio
- `src/core`: puertos/abstracciones y payloads
- `src/usecases`: casos de uso
- `src/infrastructure`: Mongo y plugins
- `src/interfaces`: API FastAPI

## Variables de entorno
- `MONGO_URI`
- `MONGO_DB`
- `MONGO_COLLECTION`

## Ejecutar local
```bash
pip install -r requirements.txt
set PYTHONPATH=.
py -m uvicorn main:app --reload
```

## API
- `POST /security/scans` (multipart form) campo `file` con JSON. Devuelve resultado en la misma respuesta.
- `GET /security/scans/{scan_id}`


