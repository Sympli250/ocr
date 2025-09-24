@echo off
REM Script d'installation complete pour Symplissime OCR
REM Realise par Ayi NEDJIMI Consultants

echo ===============================================
echo   SETUP COMPLET SYMPLISSIME OCR API
echo ===============================================

REM Verification Python
echo [CHECK] Verification Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python requis - Telechargez depuis https://python.org
    pause
    exit /b 1
)
echo [OK] Python detecte

REM Methode 1: Installation utilisateur avec --break-system-packages
echo.
echo [METHOD1] Installation avec --break-system-packages...
pip install --break-system-packages -r requirements.txt
if %errorlevel% equ 0 (
    echo [OK] Installation reussie avec --break-system-packages
    goto :test_install
)

REM Methode 2: Installation utilisateur
echo.
echo [METHOD2] Tentative installation utilisateur...
pip install --user -r requirements.txt --force-reinstall
if %errorlevel% equ 0 (
    echo [OK] Installation reussie en mode utilisateur
    goto :test_install
)

REM Methode 3: Installation une par une
echo.
echo [METHOD3] Installation package par package...
pip install --break-system-packages fastapi>=0.104.1
pip install --break-system-packages uvicorn[standard]>=0.24.0
pip install --break-system-packages paddleocr>=2.7.0
pip install --break-system-packages pdf2image>=1.16.3
pip install --break-system-packages pillow>=10.0.0
pip install --break-system-packages python-multipart>=0.0.6
pip install --break-system-packages rich>=13.0.0
pip install --break-system-packages pydantic>=2.0.0

:test_install
echo.
echo [TEST] Verification des installations...

python -c "import fastapi; print('[OK] FastAPI:', fastapi.__version__)" 2>nul || echo [WARN] FastAPI manquant
python -c "import uvicorn; print('[OK] Uvicorn disponible')" 2>nul || echo [WARN] Uvicorn manquant
python -c "import rich; print('[OK] Rich disponible')" 2>nul || echo [WARN] Rich manquant
python -c "import pydantic; print('[OK] Pydantic disponible')" 2>nul || echo [WARN] Pydantic manquant

echo.
echo [TEST] Test critique PaddleOCR...
python -c "import paddleocr; print('[OK] PaddleOCR version:', paddleocr.__version__)" 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] PaddleOCR installe et fonctionnel !
) else (
    echo [ERROR] PaddleOCR NON DISPONIBLE - API ne fonctionnera PAS
    echo [CRITICAL] Installation requise: pip install --break-system-packages paddleocr
    echo [INFO] Sans PaddleOCR, l'API retournera des erreurs 500
)

echo.
echo [TEST] Test PDF2Image...
python -c "import pdf2image; print('[OK] PDF2Image disponible')" 2>nul || echo [WARN] PDF2Image manquant

echo.
echo ===============================================
echo   INSTALLATION TERMINEE
echo ===============================================
echo [INFO] Lancez maintenant: go.bat
pause