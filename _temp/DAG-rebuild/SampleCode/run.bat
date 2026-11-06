@echo off
rem W-03 DAG visualizer demo launcher (PyQt5, conda env CPS-GPES_RPA-py311)
setlocal
set PY=C:\Users\hbk\.conda\envs\CPS-GPES_RPA-py311\python.exe
if not exist "%PY%" (
  echo [ERROR] conda env python not found: %PY%
  echo Please adjust PY in run.bat to your PyQt5-capable Python.
  pause & exit /b 1
)
cd /d "%~dp0"
if "%1"=="--offscreen" (
  "%PY%" frontend\dag_viewer.py --offscreen
) else (
  "%PY%" frontend\dag_viewer.py
)
endlocal
