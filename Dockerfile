FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
EXPOSE 8000

CMD uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
    sleep 5 && \
    streamlit run frontend/app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false --server.headless true