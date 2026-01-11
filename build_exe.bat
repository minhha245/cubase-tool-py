@echo off
echo ==================================================
echo      BUILD EXE TUDONG (AUTO-BUILDER)
echo ==================================================

echo [1/3] CAI DAT/CAP NHAT THU VIEN...
pip install customtkinter python-rtmidi pyinstaller pyautogui pygetwindow opencv-python pillow
if %errorlevel% neq 0 (
    echo LOI: Khong the cai dat thu vien. Kiem tra mang internet.
    pause
    exit /b
)

echo.
echo [2/3] DANG DONG GOI EXE (MAT KHOANG 1-2 PHUT)...
pyinstaller --noconfirm --onefile --windowed --name "BangDieuKhienAudio" --icon=NONE controller_gui.py

echo.
echo [3/3] COPY DU LIEU IMAGE...
if not exist dist mkdir dist
if exist btn_listen.png copy /Y btn_listen.png dist\
if exist btn_send.png copy /Y btn_send.png dist\

echo.
echo ==================================================
echo      HOAN TAT! FILE EXE NAM TRONG THU MUC 'dist'
echo ==================================================
pause
