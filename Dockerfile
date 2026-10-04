FROM python:3.12-slim

WORKDIR /app

# System dependencies (dla pandas/openpyxl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod aplikacji
COPY src/ ./src/
COPY config/ ./config/
COPY pyproject.toml .
COPY README.md .

# Non-root user
RUN useradd -m dqc && chown -R dqc:dqc /app
USER dqc

# Domyślna komenda — pomoc
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]