#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/pyinstaller --noconfirm --windowed --name Coeus \
  --add-data "web:web" --paths . \
  --osx-bundle-identifier com.coeus.desktop \
  desktop_entry.py
echo "Built dist/Coeus.app"
