FROM python:3.12-slim-bookworm

WORKDIR /iris-wallet-vault

# Install poetry
RUN python3 -m pip install --no-cache-dir poetry

# Install system dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        binutils file sudo wget \
        libasound2 \
        libatk1.0-0 \
        libatomic1 \
        libcairo-gobject2 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libegl1 \
        libfontconfig1 \
        libfuse2 \
        libgdk-pixbuf-2.0-0 \
        libgl1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpulse0 \
        libwayland-cursor0 \
        libwayland-egl1 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-keysyms1 \
        libxcb-shape0 \
        libxcb-xkb1 \
        libxcomposite1 \
        libxdamage1 \
        libxi6 \
        libxkbcommon-x11-0 \
        libxkbcommon0 \
        libxkbfile1 \
        libxrandr2 \
        libxrender1 \
        libxtst6 \
        meson \
        build-essential \
        gcc \
        libcairo2-dev \
        pkg-config \
        python3-dev \
        libgirepository1.0-dev \
        curl \
        git \
        ca-certificates

# Copy project code
COPY . .

# Install project dependencies via Poetry
RUN poetry install

# Setup the entrypoint
RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]
