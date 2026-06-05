@echo off
setlocal
:: Garantir que o script rode na pasta onde ele está localizado
cd /d "%~dp0"
title Instalador Notch Win

set LOG_FILE=%~dp0instalacao_erro.log

echo ===================================================
echo           ASSISTENTE DE INSTALACAO NOTCH
echo ===================================================
echo.

:: 1. Tentar detectar o Python no PATH
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

:: 2. Procurar Python em caminhos de instalação conhecidos (user e machine)
for %%V in (313 312 311 310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :START_WIZARD
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        set "PY_CMD=C:\Program Files\Python%%V\python.exe"
        goto :START_WIZARD
    )
    if exist "C:\Python%%V\python.exe" (
        set "PY_CMD=C:\Python%%V\python.exe"
        goto :START_WIZARD
    )
)

:: 3. Se nao encontrou, tentar instalar via Winget (--scope user, sem precisar de admin)
echo [AVISO] Python nao encontrado no sistema.
echo Tentando instalar o Python automaticamente via Winget...
echo.

winget --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERRO] Nao foi possivel encontrar o instalador automatico (Winget).
    echo Por favor, instale o Python manualmente em: https://www.python.org/
    call :WRITE_LOG "Winget nao encontrado. Python nao pode ser instalado automaticamente."
    pause
    exit /b 1
)

echo Instalando Python 3.12... Aguarde, isso pode levar alguns minutos.
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
if %errorlevel% NEQ 0 (
    echo.
    echo [ERRO] A instalacao automatica falhou.
    echo Tente baixar manualmente em python.org e marque a opcao "Add Python to PATH".
    call :WRITE_LOG "Falha ao instalar Python via Winget. Codigo de erro: %errorlevel%"
    pause
    exit /b 1
)

:: 4. Após instalar, localizar o executável diretamente (PATH pode não ter atualizado ainda)
echo.
echo [OK] Python instalado! Localizando o executavel...
for %%V in (313 312 311 310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :START_WIZARD
    )
)

echo [ERRO] Python foi instalado mas o executavel nao foi localizado.
echo Por favor, feche e reabra o instalador.
call :WRITE_LOG "Python instalado via winget mas executavel nao localizado nos paths conhecidos."
pause
exit /b 1

:START_WIZARD
echo [OK] Python detectado:
"%PY_CMD%" --version
echo.
echo Iniciando assistente visual...
"%PY_CMD%" "%~dp0installer\setup_wizard.py"
if %errorlevel% NEQ 0 (
    echo.
    echo [ERRO] Houve um problema ao abrir o assistente.
    call :WRITE_LOG "Falha ao executar setup_wizard.py. Codigo de erro: %errorlevel%"
    pause
)

endlocal
exit /b

:WRITE_LOG
setlocal
set MSG=%~1
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set DATA=%%c-%%b-%%a
for /f "tokens=1-2 delims=: " %%a in ("%time%") do set HORA=%%a:%%b
echo [%DATA% %HORA%] %MSG% >> "%LOG_FILE%"
echo Log de erro gerado em: %LOG_FILE%
endlocal
exit /b
