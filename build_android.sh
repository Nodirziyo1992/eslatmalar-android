#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v buildozer >/dev/null 2>&1; then
  echo "Buildozer o‘rnatilmagan. README.md ko‘rsatmalarini bajaring."
  exit 1
fi
buildozer -v android debug
printf '\nAPK fayllari bin/ papkasida.\n'
