@echo off
echo ===============================================
echo   FIX PYTORCH DLL ISSUE - PADDLEOCR
echo ===============================================

echo [INFO] Probleme identifie: PyTorch DLL shm.dll conflict
echo [INFO] Erreur: "Error loading shm.dll or one of its dependencies"

echo.
echo [FIX1] Desinstallation et reinstallation PyTorch CPU...

REM Supprimer torch problematique
pip uninstall -y torch torchvision torchaudio

REM Installer PyTorch CPU uniquement (plus stable)
pip install --break-system-packages torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo [FIX2] Reinstallation PaddleOCR avec nouvelle version PyTorch...
pip install --break-system-packages --force-reinstall paddleocr

echo.
echo [TEST] Test complet...
python -c "import torch; print('[OK] PyTorch version:', torch.__version__)"
python -c "import paddle; print('[OK] PaddlePaddle version:', paddle.__version__)"
python -c "import paddleocr; print('[OK] PaddleOCR version:', paddleocr.__version__)"

echo.
echo [TEST] Test initialisation OCR...
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='fr'); print('[SUCCESS] Initialisation OK')"

echo.
echo ===============================================
echo   FIX TERMINE
echo ===============================================
echo [INFO] Si ca marche, relancez: go.bat
pause