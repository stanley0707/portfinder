FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data

RUN pip install git+https://github.com/stanley0707/portfinder.git@


ENTRYPOINT ["portfinder"]