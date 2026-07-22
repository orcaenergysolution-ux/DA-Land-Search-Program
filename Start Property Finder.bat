@echo off
setlocal enabledelayedexpansion
title Property Finder
cd /d "%~dp0"

echo.
echo   Starting the Property Finder...
echo.

set "PY="

REM --- 1) Official Python launcher (py.exe) -------------------------------
for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"

REM --- 2) python on PATH (skips the Microsoft Store stub, which errors) ---
if not defined PY (
  for /f "delims=" %%P in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"
)

REM --- 3) Common install locations ----------------------------------------
if not defined PY (
  for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
  )
)
if not defined PY (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
  )
)
if not defined PY (
  for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
  )
)
if not defined PY (
  for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" set "PY=%%D\python.exe"
  )
)

if not defined PY (
  echo   ---------------------------------------------------------------
  echo   Python was not found on this computer.
  echo.
  echo   Install it from:  https://www.python.org/downloads/
  echo   IMPORTANT: tick "Add Python to PATH" on the first install screen.
  echo.
  echo   Then run this file again.
  echo   ---------------------------------------------------------------
  echo.
  pause
  exit /b 1
)

if not exist "src\web_app.py" (
  echo   ---------------------------------------------------------------
  echo   Could not find src\web_app.py next to this file.
  echo   Keep this .bat inside the project folder.
  echo   Current folder: %CD%
  echo   ---------------------------------------------------------------
  echo.
  pause
  exit /b 1
)

echo   Using Python: !PY!
echo.
echo   Your browser will open automatically.
echo.
echo   KEEP THIS WINDOW OPEN while you use the program.
echo   Close this window when you are finished.
echo.

"!PY!" "src\web_app.py"

if errorlevel 1 (
  echo.
  echo   The program stopped unexpectedly. Details are above.
  echo.
  pause
)
