@echo off
echo ===============================================
echo   INSTALLATION COMPLETE PADDLEOCR + PADDLE
echo ===============================================

echo [INFO] Le probleme identifie: PaddleOCR necessite PaddlePaddle
echo [INFO] Erreur: "No module named 'paddle'"

echo.
echo [INSTALL] Installation PaddlePaddle (dependance de PaddleOCR)...

REM Installation de PaddlePaddle d'abord
pip install --break-system-packages paddlepaddle-gpu 2>nul
if %errorlevel% neq 0 (
    echo [WARN] GPU version echouee, tentative CPU...
    pip install --break-system-packages paddlepaddle
)

REM Puis PaddleOCR
echo [INSTALL] Installation PaddleOCR...
pip install --break-system-packages paddleocr pdf2image

REM Test final
echo.
echo [TEST] Test complet...
python -c "import paddle; print('[OK] PaddlePaddle version:', paddle.__version__)"
python -c "import paddleocr; print('[OK] PaddleOCR version:', paddleocr.__version__)"

echo.
echo [TEST] Test initialisation OCR...
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='fr'); print('[SUCCESS] Initialisation OK')"

echo.
echo ===============================================
echo   INSTALLATION TERMINEE
echo ===============================================
echo [INFO] Relancez maintenant: go.bat
pause