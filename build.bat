@echo off
title Compilador MSRA Automator
echo ===================================================
echo   Compilador Automático do MSRA Automator
echo ===================================================
echo.

:: Verifica se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não foi encontrado no PATH do sistema.
    echo Por favor, instale o Python 3.8+ e marque a opção "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/4] Instalando/Atualizando dependências de compilação...
python -m pip install --upgrade pip
python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao tentar instalar/atualizar o PyInstaller/pip globalmente.
    echo Tentando continuar mesmo assim...
)

echo.
echo [2/4] Instalando dependências do projeto (requirements.txt)...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependências do requirements.txt.
    echo Verifique sua conexão com a internet.
    pause
    exit /b 1
)

echo.
echo [3/4] Compilando o executável com PyInstaller...
:: Explicação dos parâmetros:
:: --onefile: Gera um único arquivo executável (.exe)
:: --noconsole: Oculta a janela preta do prompt de comando ao abrir a aplicação gráfica
:: --name "MSRA Automator": Define o nome do executável gerado
:: --clean: Limpa o cache do PyInstaller antes do build
pyinstaller --clean --onefile --noconsole --name "MSRA Automator" main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha na compilação do executável com PyInstaller.
    pause
    exit /b 1
)

echo.
echo [4/4] Organizando os arquivos finais...
if exist "dist\MSRA Automator.exe" (
    copy "dist\MSRA Automator.exe" "MSRA Automator.exe" >nul
    echo.
    echo ===================================================
    echo [SUCESSO] MSRA Automator compilado com sucesso!
    echo O arquivo "MSRA Automator.exe" foi copiado para a raiz.
    echo ===================================================
) else (
    echo [ERRO] O executável compilado não foi encontrado na pasta 'dist'.
)

echo.
echo Pressione qualquer tecla para sair...
pause >nul
