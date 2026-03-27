@echo off
echo ============================================
echo  Data Network Visualization Tool
echo ============================================
echo.
echo Installing required packages...
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Please check Python installation.
    pause
    exit /b 1
)
echo.
echo Starting server... (http://localhost:8000)
echo Press Ctrl+C to stop.
echo.
python app.py
pause
