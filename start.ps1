# Stock Analysis AI - Quick Start Script (Windows PowerShell)
# This script automates the setup and running of the application

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Stock Analysis AI - Quick Start" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

function Require-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Required command not found: $name"
  }
}

Write-Host "Checking Python installation..." -ForegroundColor Yellow
Require-Command "python"
Write-Host ("? Python found: " + (python --version)) -ForegroundColor Green

Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
Require-Command "node"
Write-Host ("? Node.js found: " + (node --version)) -ForegroundColor Green

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Backend Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\backend"

if (-not (Test-Path -Path ".\venv")) {
  Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
  python -m venv venv
  Write-Host "? Virtual environment created" -ForegroundColor Green
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
. .\venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
Write-Host "? Dependencies installed" -ForegroundColor Green

New-Item -ItemType Directory -Force -Path ".\static\charts" | Out-Null
New-Item -ItemType Directory -Force -Path ".\ml\models" | Out-Null

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Frontend Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\frontend"

if (-not (Test-Path -Path ".\node_modules")) {
  Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
  npm install
  Write-Host "? Dependencies installed" -ForegroundColor Green
} else {
  Write-Host "? Dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Starting Application" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\backend"
. .\venv\Scripts\Activate.ps1

Write-Host "Starting Flask backend on http://localhost:5000" -ForegroundColor Green
$backend = Start-Process -FilePath "python" -ArgumentList "app.py" -PassThru

Start-Sleep -Seconds 2

Set-Location -Path "$PSScriptRoot\frontend"
Write-Host "Starting React frontend on http://localhost:3000" -ForegroundColor Green
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
Start-Process "http://localhost:3000"

try {
  npm start
} finally {
  if ($backend -and -not $backend.HasExited) {
    Stop-Process -Id $backend.Id -Force
  }
}
