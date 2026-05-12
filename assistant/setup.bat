@echo off
echo ============================================
echo    A.N.T.O.I.N.E V1.1 - Installation
echo ============================================
echo.

echo Verification de Python...
python --version
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH.
    echo Telecharge Python 3.10+ sur https://python.org
    pause
    exit /b 1
)

echo.
echo Installation des dependances Python...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ATTENTION: Une erreur s'est produite.
    echo Si PyAudio echoue, essayez:
    echo   pip install pipwin
    echo   pipwin install pyaudio
    echo.
    echo Ou telechargez le wheel PyAudio depuis:
    echo   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
)

echo.
echo Copie du fichier de configuration...
if not exist .env (
    copy .env.example .env
    echo Fichier .env cree. Editez-le avec vos cles API.
) else (
    echo Fichier .env deja present.
)

echo.
echo ============================================
echo    Installation terminee !
echo.
echo    Etapes suivantes :
echo    1. Ouvrez le fichier .env
echo    2. Ajoutez au moins une cle API (GEMINI, GROQ ou ANTHROPIC)
echo    3. Lancez run.bat pour demarrer A.N.T.O.I.N.E
echo ============================================
pause
