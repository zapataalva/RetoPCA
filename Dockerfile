FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app
ENV MONGO_URL=mongodb://mongodb:27017
ENV MONGO_DB=dast_scanner
ENV MONGO_COLLECTION=results

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
