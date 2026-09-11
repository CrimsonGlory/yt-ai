#!/bin/sh
set -eu

if [ -n "${SKIP_ONEFILE_BUILD:-}" ]; then
    if [ -n "${SKIP_ONEDIR_BUILD:-}" ]; then
        echo "All executable builds were skipped"
        exit 1
    fi
    echo "Extracting zip to verify onedir build"
    if command -v python3 >/dev/null 2>&1; then
        python3 -m zipfile -e "/build/${EXE_NAME}.zip" ./
    else
        echo "Attempting to install unzip"
        if command -v dnf >/dev/null 2>&1; then
            dnf -y install --allowerasing unzip
        elif command -v yum >/dev/null 2>&1; then
            yum -y install unzip
        elif command -v apt-get >/dev/null 2>&1; then
            # Debian 11 (bullseye) LTS ended 2026-08-31. The last
            # bullseye-security InRelease is Valid-Until 2026-09-07, after
            # which apt-get update fails with exit 100 and blocks releases.
            apt_update() {
                DEBIAN_FRONTEND=noninteractive apt-get \
                    -o Acquire::Check-Valid-Until=false \
                    update -qq
            }
            if ! apt_update; then
                echo "apt-get update failed; retrying via archive.debian.org without security"
                if [ -f /etc/apt/sources.list ]; then
                    sed -i \
                        -e '/security/d' \
                        -e 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' \
                        /etc/apt/sources.list
                fi
                if [ -d /etc/apt/sources.list.d ]; then
                    for src in /etc/apt/sources.list.d/*; do
                        [ -f "${src}" ] || continue
                        if grep -q security "${src}"; then
                            rm -f "${src}"
                        else
                            sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' "${src}"
                        fi
                    done
                fi
                apt_update
            fi
            DEBIAN_FRONTEND=noninteractive apt-get \
                -o Acquire::Check-Valid-Until=false \
                install -qq -y --no-install-recommends unzip
        elif command -v apk >/dev/null 2>&1; then
            apk add --no-cache unzip
        else
            echo "Unsupported image"
            exit 1
        fi
        unzip "/build/${EXE_NAME}.zip" -d ./
    fi
    chmod +x "./${EXE_NAME}"
    "./${EXE_NAME}" -v || true
    "./${EXE_NAME}" --version
    exit 0
fi

echo "Verifying onefile build"
cp "/build/${EXE_NAME}" ./
chmod +x "./${EXE_NAME}"

if [ -z "${UPDATE_TO:-}" ]; then
    "./${EXE_NAME}" -v || true
    "./${EXE_NAME}" --version
    exit 0
fi

cp "./${EXE_NAME}" "./${EXE_NAME}_downgraded"
version="$("./${EXE_NAME}" --version)"
"./${EXE_NAME}_downgraded" -v --update-to "${UPDATE_TO}"
downgraded_version="$("./${EXE_NAME}_downgraded" --version)"
if [ "${version}" = "${downgraded_version}" ]; then
    exit 1
fi
