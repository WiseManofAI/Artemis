@echo off
echo [*] Setting up virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [*] Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt
echo [*] Starting server...
uvicorn main:app --reload
