@echo off
title Inventario Lovo - Lanzador
color 0A

echo =========================================
echo      INICIANDO INVENTARIO LOVO
echo =========================================
echo.

echo [1/3] Instalando dependencias...
pip install -r requirements.txt -q
echo.

echo [2/3] Iniciando Servidor Backend (API)...
start "Servidor Backend - Inventario Lovo" cmd /k "python server.py"

echo [3/3] Iniciando Servidor Frontend (PWA)...
start "Servidor Frontend - Inventario Lovo" cmd /c "python -m http.server 5500"

echo.
echo Esperando unos segundos para que los servidores arranquen...
timeout /t 3 /nobreak > nul

echo Abriendo el navegador web...
start chrome --incognito "http://localhost:5500/index.html?t=%RANDOM%"
if errorlevel 1 (
    start msedge -inprivate "http://localhost:5500/index.html?t=%RANDOM%"
)

echo.
echo =========================================
echo  APLICACION INICIADA CORRECTAMENTE
echo =========================================
echo Puedes cerrar esta ventana negra.
timeout /t 3 > nul
exit
