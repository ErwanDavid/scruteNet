# Launcher for analyseConn.py - PowerShell version
# Uses .venv if present, otherwise uses system python. Run in PowerShell (may require ExecutionPolicy change).
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPython = "C:\Users\erwan\venv_net\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython (Join-Path $scriptDir 'analyseConn.py') @args
} else {
    python (Join-Path $scriptDir 'analyseConn.py') @args
}
