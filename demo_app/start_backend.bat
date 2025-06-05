@echo off
echo Starting PDF Processor Backend...
echo.

cd backend

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Starting Flask application...
echo Backend will be available at http://localhost:5000
echo.

python app.py

pause 