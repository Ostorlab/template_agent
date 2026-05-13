FROM python:3.14-bookworm as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --prefix=/install -r /requirements.txt

FROM base
RUN apt-get update && apt-get install -y openjdk-17-jdk android-sdk
COPY --from=builder /install /usr/local
RUN mkdir -p /app/agent
ENV PYTHONPATH=/app
COPY agent /app/agent
COPY oxo.yaml /app/agent/oxo.yaml
WORKDIR /app
CMD ["python", "/app/agent/anti_tampering_agent.py"]
