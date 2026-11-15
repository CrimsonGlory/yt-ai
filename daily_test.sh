#!/usr/bin/env bash
# Daily full-suite run: make test, log results, Grok-fix failures and commit.
#
# Runs `make test` (pytest -Werror + ruff/autopep8). If anything failed, launches
# one always-approve Grok session with the failure list and the log path.
# Each independent fix (usually one extractor) is a separate commit; a leftover
# combined commit is split. Does not push. Skips Grok when the suite is already
# green.
#
# Crontab (once a day). Schedule *after* pull_upstream.sh so a merge is not in
# progress during the ~3h suite, e.g. 08:00 local time:
#   0 8 * * * /path/to/yt-ai/daily_test.sh
#
# Optional environment:
#   GROK_BIN, GROK_MODEL
#   YT_AI_VENV          venv to activate (default: $repo/.venv or $repo/venv)
#
# Extra args are forwarded to devscripts/daily_test.py
#   ./daily_test.sh --dry-run
#   ./daily_test.sh --no-grok
#   ./daily_test.sh --from-log tmp/daily-test/pytest-latest.log
set -euo pipefail

# Cron has a tiny PATH.
export PATH="/usr/local/bin:/usr/bin:/bin:${HOME}/.local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ -n "${YT_AI_VENV:-}" && -f "${YT_AI_VENV}/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source "${YT_AI_VENV}/bin/activate"
    elif [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source "${SCRIPT_DIR}/.venv/bin/activate"
    elif [[ -f "${SCRIPT_DIR}/venv/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source "${SCRIPT_DIR}/venv/bin/activate"
    fi
fi

LOG_DIR="${SCRIPT_DIR}/tmp/daily-test"
mkdir -p "${LOG_DIR}"

LOCK="${LOG_DIR}/daily_test.lock"
exec 9>"${LOCK}"
if ! flock -n 9; then
    echo "$(date -Iseconds) another daily_test is already running; exiting" >&2
    exit 0
fi

STAMP="$(date +%Y-%m-%dT%H%M%S)"
RUN_LOG="${LOG_DIR}/cron-${STAMP}.log"

set +e
{
    echo "=== daily_test ${STAMP} pwd=${SCRIPT_DIR} python=$(command -v python3) ==="
    python3 "${SCRIPT_DIR}/devscripts/daily_test.py" \
        --log-dir "${LOG_DIR}" \
        "$@"
} 2>&1 | tee -a "${RUN_LOG}"
rc=${PIPESTATUS[0]}
set -e

# Keep a stable "latest" pointer for tailing.
ln -sfr "${RUN_LOG}" "${LOG_DIR}/cron-latest.log" 2>/dev/null || \
    cp -f "${RUN_LOG}" "${LOG_DIR}/cron-latest.log"

# Drop cron/pytest/grok logs older than 30 days; keep progress.jsonl.
find "${LOG_DIR}" -maxdepth 1 -type f -name 'cron-*.log' -mtime +30 -delete || true
find "${LOG_DIR}" -maxdepth 1 -type f -name 'pytest-*.log' -mtime +30 -delete || true
find "${LOG_DIR}" -maxdepth 1 -type f -name 'pytest-*.xml' -mtime +30 -delete || true
find "${LOG_DIR}" -maxdepth 1 -type f -name 'prompt-*.txt' -mtime +30 -delete || true
find "${LOG_DIR}" -maxdepth 1 -type f -name 'summary-*.json' -mtime +30 -delete || true
find "${LOG_DIR}/grok" -maxdepth 1 -type f -name '*.log' -mtime +30 -delete 2>/dev/null || true

exit "${rc}"
