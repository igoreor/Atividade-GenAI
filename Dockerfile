FROM python:3.11-slim

WORKDIR /app

# Instala dependências primeiro (aproveita cache de layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte e os dados
COPY dados/ dados/
COPY scripts/ scripts/
COPY backend/ backend/
COPY .env.example .env.example

# Gera o banco.db a partir dos CSVs durante o build
RUN python scripts/build_db.py

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
