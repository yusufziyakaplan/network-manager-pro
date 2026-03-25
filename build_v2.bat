@echo off
echo ========================================
echo  Network Manager Pro v2 - EXE Builder
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Eski EXE siliniyor...
if exist dist\NetworkManagerProV2.exe (
    del /f dist\NetworkManagerProV2.exe
    if exist dist\NetworkManagerProV2.exe (
        echo HATA: EXE silinemedi. Programi kapatip tekrar deneyin.
        pause
        exit
    )
)
echo.

echo [2/3] EXE olusturuluyor...
"C:\Program Files\Python313\python.exe" -m PyInstaller --onefile --noconsole ^
    --name=NetworkManagerProV2 ^
    --manifest=admin.manifest ^
    --hidden-import=pystray._win32 ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=win32com.client ^
    --hidden-import=win32com.shell ^
    --hidden-import=pythoncom ^
    --hidden-import=pywintypes ^
    network_manager_pro2.py

echo.
echo [3/3] Temizlik...
if exist build rmdir /s /q build
if exist NetworkManagerProV2.spec del NetworkManagerProV2.spec
echo.

if exist dist\NetworkManagerProV2.exe (
    echo ========================================
    echo  BASARILI!
    echo ========================================
    echo.
    echo EXE: %~dp0dist\NetworkManagerProV2.exe
    echo.
    dir dist\NetworkManagerProV2.exe | find "NetworkManagerProV2.exe"
) else (
    echo ========================================
    echo  HATA! EXE olusturulamadi.
    echo ========================================
)
echo.
pause
