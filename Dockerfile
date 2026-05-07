FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge.py .

ENV CONFIG_PATH=/config/config.yaml

CMD ["python", "bridge.py"]
