#Requires -Version 5.1
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

Write-Info "Checking Python 3.11 or newer..."
$python = Find-Python
if (-not $python) {
    throw "Python 3.11 or newer is required (official CPython). MSYS2 Python is not supported because several development wheels are unavailable."
}

$pythonVersion = & $python.Command @($python.Arguments + @("-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"))
Write-Info "Using interpreter: $($python.Command) $($python.Arguments -join ' ') ($pythonVersion)"

$venvPython = Get-VenvPython
if (-not $venvPython) {
    Write-Info "Creating virtual environment at .venv..."
    & $python.Command @($python.Arguments + @("-m", "venv", (Join-Path $Root ".venv")))
    $venvPython = Get-VenvPython
} else {
    Write-Info "Virtual environment already exists; reusing it."
}

if (-not $venvPython) {
    throw "Could not find the virtual environment interpreter."
}

Write-Info "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

Write-Info "Installing VoiceStock with development dependencies..."
& $venvPython -m pip install -e ".[dev]"

Write-Info "Installing pre-commit hooks..."
& $venvPython -m pre_commit install

Write-Info "Setup completed successfully."
Write-Info "Activate the environment with:"
Write-Info "  .venv\Scripts\Activate.ps1"
Write-Info "Then run: ruff check . && pytest"
