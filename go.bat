@echo off
REM Realise par Ayi NEDJIMI Consultants
echo ===============================================
echo      SYMPLISSIME OCR API - Demarrage
echo ===============================================

REM Verification de Python
echo [CHECK] Verification Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python n'est pas installe ou pas dans le PATH
    echo [INFO] Telechargez Python depuis https://python.org
    pause
    exit /b 1
) else (
    echo [OK] Python detecte
)

REM Verification et installation des dependances
echo.
echo [DEPS] Verification des dependances Python...

REM Test rapide PaddleOCR (sans installation systematique)
echo [CHECK] Test PaddleOCR rapide...
python -c "import paddleocr; print('[OK] PaddleOCR disponible')" 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] PaddleOCR manquant - lancement installation...
    python install_paddleocr.py
) else (
    echo [OK] PaddleOCR deja disponible
)

REM Si echec, installation de base sans PaddleOCR
echo [FALLBACK] Installation des dependances de base...
pip install --break-system-packages fastapi uvicorn pillow python-multipart rich pydantic 2>nul
if %errorlevel% neq 0 (
    pip install --user fastapi uvicorn pillow python-multipart rich pydantic 2>nul
)

REM Copie du fichier de test vers XAMPP
echo.
echo [XAMPP] Copie du fichier de test vers XAMPP...
if exist "testocr.php" (
    if exist "C:\xampp2\htdocs\" (
        copy /Y "testocr.php" "C:\xampp2\htdocs\testocr.php" >nul
        echo [OK] testocr.php copie vers C:\xampp2\htdocs\
        echo [WEB] Acces test: http://localhost/testocr.php
    ) else (
        if exist "C:\xampp\htdocs\" (
            copy /Y "testocr.php" "C:\xampp\htdocs\testocr.php" >nul
            echo [OK] testocr.php copie vers C:\xampp\htdocs\
            echo [WEB] Acces test: http://localhost/testocr.php
        ) else (
            echo [WARN] Repertoire XAMPP non trouve (ni xampp ni xampp2)
        )
    )
) else (
    echo [WARN] Fichier testocr.php non trouve
)

echo.
REM Test des dependances
echo [TEST] Test rapide des dependances...
python -c "import fastapi, uvicorn, rich; print('[OK] Dependances de base OK')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Dependances de base manquantes
    pause
    exit /b 1
)

python -c "import paddleocr; print('[OK] PaddleOCR disponible')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PaddleOCR NON DISPONIBLE - API ne fonctionnera pas
    echo [INFO] Installez avec: pip install --break-system-packages paddleocr
    echo [INFO] Ou executez: setup_env.bat
) else (
    echo [OK] PaddleOCR disponible
)

echo.
REM Demarrage du serveur
echo [START] Demarrage du serveur OCR...
echo ===============================================
python start.py

REM Pause pour voir les erreurs eventuelles
echo.
echo ===============================================
echo   Serveur arrete - Verifiez les messages
echo ===============================================
pause
