# Build Coeus.exe on Windows. Run this from the coeus folder in PowerShell.
# A Mac cannot produce this file. The script is the Windows app build.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\pyinstaller --noconfirm --windowed --name Coeus --add-data "web;web" --paths . desktop_entry.py
Write-Host "Built dist\Coeus\Coeus.exe"
