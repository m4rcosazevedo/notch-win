@echo off
setlocal
:: Garantir que o script rode na pasta onde ele está localizado
cd /d "%~dp0"
title Instalador Notch Win

echo ===================================================
echo           ASSISTENTE DE INSTALACAO NOTCH
echo ===================================================
echo.

:: 1. Tentar detectar o Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PY_CMD=python
    goto :START_WIZARD
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    set PY_CMD=py
    goto :START_WIZARD
)

:: 2. Se nao encontrou, tentar instalar via Winget (Windows 10/11)
echo [AVISO] Python nao encontrado no sistema.
echo Tentando instalar o Python automaticamente via Winget...
echo.

winget --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERRO] Nao foi possivel encontrar o instalador automatico (Winget).
    echo Por favor, instale o Python manualmente em: https://www.python.org/
    pause
    exit /b
)

echo Instalando Python 3.12... Aguarde, isso pode levar alguns minutos.
winget install -e --id Python.Python.3.12 --scope machine --accept-package-agreements --accept-source-agreements
if %errorlevel% NEQ 0 (
    echo.
    echo [ERRO] A instalacao automatica falhou. 
    echo Tente baixar manualmente em python.org e marque a opcao "Add Python to PATH".
    pause
    exit /b
)

echo.
echo [OK] Python instalado! Reiniciando o script para aplicar as mudancas...
timeout /t 3
"%~f0"
exit /b

:START_WIZARD
echo [OK] Python detectado: 
%PY_CMD% --version
echo.
echo Iniciando assistente visual...
"%PY_CMD%" "%~dp0installer\setup_wizard.py"
if %errorlevel% NEQ 0 (
    echo.
    echo [ERRO] Houve um problema ao abrir o assistente.
    pause
)

endlocal
