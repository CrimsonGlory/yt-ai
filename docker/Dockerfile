# Development image: project + default extras + curl_cffi + offline test deps.
# Binary packaging remains under bundle/docker; this is not a release builder.
FROM python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /src

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY yt_dlp ./yt_dlp
COPY test ./test
COPY devscripts ./devscripts

RUN pip install --no-cache-dir \
        ".[default,curl-cffi]" \
        "pytest~=9.0" \
        "pytest-rerunfailures~=16.0" \
        "pytest-cov" \
        "coverage"

CMD ["python", "-m", "yt_dlp", "--version"]
