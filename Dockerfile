FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        iptables \
        gdb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/vcd-sidecar

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

RUN mkdir -p /var/vcd/forensics

ENV VCD_WEBHOOK_PORT=8888 \
    VCD_FORENSICS_DIR=/var/vcd/forensics \
    VCD_MEMORY_DUMP=false \
    VCD_TERMINATE_MODE=graceful \
    VCD_TERMINATE_TIMEOUT=30

EXPOSE 8888

CMD ["python", "-m", "app.main"]
