FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    net-tools \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir portfinder


ENTRYPOINT ["portfinder"]