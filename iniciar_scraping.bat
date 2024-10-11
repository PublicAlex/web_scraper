@echo off
REM Script para ejecutar app.py y mostrar la consola con los prints

REM Verifica si Python está instalado
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python no está instalado. Por favor, instala Python antes de continuar.
    exit /b
)

REM Ejecuta el script app.py y muestra la salida en la consola
echo Ejecutando app.py...
python app.py

REM Mantiene la consola abierta después de la ejecución
echo Presiona cualquier tecla para cerrar la consola...
pause
