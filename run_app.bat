@echo off
REM Launcher for analyseConn.py - uses .venv if available, otherwise system python
setlocal
set SCRIPT_DIR=%~dp0
set VENV_PY=C:\Users\erwan\venv_net\Scripts\python.exe
n
if exist "%VENV_PY%" (
    "%VENV_PY%" "%SCRIPT_DIR%analyseConn.py" %*
) else (
    python "%SCRIPT_DIR%analyseConn.py" %*
)
endlocal
