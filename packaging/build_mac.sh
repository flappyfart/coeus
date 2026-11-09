#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/pyinstaller --noconfirm --windowed --name Coeus \
  --add-data "web:web" --paths . \
  --osx-bundle-identifier com.coeus.desktop \
  --hidden-import eth_account \
  --hidden-import hyperliquid.exchange \
  --hidden-import hyperliquid.utils.signing \
  --collect-submodules hyperliquid \
  --collect-submodules eth_account \
  --collect-submodules webview \
  desktop_entry.py
echo "Built dist/Coeus.app"
