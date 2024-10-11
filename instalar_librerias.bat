@echo off
REM Script para instalar las librerías de Python necesarias

REM Verifica si Python está instalado
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python no está instalado. Iniciando la descarga de Python...
    REM Descargar el instalador de Python
    curl -o python-installer.exe https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe
    

)

REM Instala las librerías necesarias
echo Instalando las librerías necesarias...
pip install requests beautifulsoup4 lxml jsonschema xmltodict

echo Instalación completada.
pause
