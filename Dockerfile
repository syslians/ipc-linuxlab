FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       make \
       python3 \
       python3-pytest \
       strace \
       iproute2 \
       procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . /workspace
RUN make all

CMD ["bash"]
