@echo off
title Compartir Lovo por Internet (Cloudflare)
color 0B

echo =========================================
echo   COMPARTIENDO INVENTARIO LOVO A INTERNET
echo =========================================
echo.
echo 1. Asegurate de que el servidor ya esta iniciado (con iniciar_app.bat)
echo 2. Se va a generar un enlace seguro HTTPS (terminado en .trycloudflare.com)
echo 3. Copia ese enlace y enviaselo a los camareros.
echo.
echo Iniciando túnel... (Puede tardar unos segundos)
echo.

.\cloudflared.exe tunnel --url http://localhost:8000

pause
