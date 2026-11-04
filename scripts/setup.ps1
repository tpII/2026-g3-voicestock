#Requires -Version 5.1
param([switch]$Stt)
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Write-Info {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Test-PythonUsable {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Arguments = @()
    )

    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        return $false
    }

    $code = @"
import sys, sysconfig
plat = sysconfig.get_platform().lower()
ok = sys.version_info >= (3, 11) and 'mingw' not in plat and 'cygwin' not in plat
raise SystemExit(0 if ok else 1)
"@
    $allArguments = @($Arguments) + @("-c", $code)
    & $Command @allArguments 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Find-Python {
    $candidates = @(
        @{ Command = "py"; Arguments = @("-3.11") },
        @{ Command = "python3.11"; Arguments = @() },
        @{ Command = "python3"; Arguments = @() },
        @{ Command = "python"; Arguments = @() },
        @{ Command = "py"; Arguments = @("-3") }
    )

    foreach ($candidate in $candidates) {
        if (Test-PythonUsable -Command $candidate.Command -Arguments $candidate.Arguments) {
            return $candidate
        }
    }

    return $null
}

function Get-VenvPython {
    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $posixPython = Join-Path $Root ".venv\bin\python"
    if (Test-Path $posixPython) {
        return $posixPython
    }

    return $null
}

if ($env:CONDA_PREFIX) {
    $environmentPython = $null
    foreach ($candidate in @(
        (Join-Path $env:CONDA_PREFIX "python.exe"),
        (Join-Path $env:CONDA_PREFIX "bin/python")
    )) {
        if ((Test-Path $candidate) -and (Test-PythonUsable -Command $candidate)) {
            $environmentPython = $candidate
            break
        }
    }
    if (-not $environmentPython) {
        throw "The active Conda environment must provide compatible Python 3.11 or newer."
    }
    Write-Info "Using active Conda environment: $env:CONDA_PREFIX"
} else {
    Write-Info "Checking Python 3.11 or newer..."
    $python = Find-Python
    if (-not $python) {
        throw "Python 3.11 or newer is required (official CPython). MSYS2 Python is not supported."
    }
    $environmentPython = Get-VenvPython
    if (-not $environmentPython) {
        Write-Info "Creating virtual environment at .venv..."
        & $python.Command @($python.Arguments + @("-m", "venv", (Join-Path $Root ".venv")))
        if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
        $environmentPython = Get-VenvPython
    } else {
        Write-Info "Virtual environment already exists; reusing it."
    }
    if (-not $environmentPython) {
        throw "Could not find the virtual environment interpreter."
    }
}
Write-Info "Using interpreter: $environmentPython"
$installExtras = if ($Stt) { "dev,stt-vosk" } else { "dev" }

Write-Info "Upgrading pip..."
& $environmentPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }

Write-Info "Installing VoiceStock with development dependencies..."
& $environmentPython -m pip install -e ".[$installExtras]"
if ($LASTEXITCODE -ne 0) { throw "Could not install VoiceStock dependencies." }

Write-Info "Installing pre-commit hooks..."
& $environmentPython -m pre_commit install
if ($LASTEXITCODE -ne 0) { throw "Could not install pre-commit hooks." }

Write-Info "Setup completed successfully."
if ($env:CONDA_PREFIX) {
    Write-Info "Conda environment is already active."
} else {
    Write-Info "Activate the environment with: .venv\Scripts\Activate.ps1"
}
Write-Info "Then run: ruff check . && pytest"
