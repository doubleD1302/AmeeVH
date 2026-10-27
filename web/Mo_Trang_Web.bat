@echo off
chcp 65001 >nul
title Stella Sora - Web Tải Launcher Việt Hóa
cd /d "%~dp0"
echo ========================================================
echo   Khởi động Web Tải Launcher Stella Sora Việt Hóa
echo ========================================================
echo.

set "PY_EXE="
if exist "..\..\.venv\Scripts\python.exe" (
    set "PY_EXE=..\..\.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            set "PY_EXE=py"
        )
    )
)

if defined PY_EXE (
    echo [1/2] Tìm thấy môi trường Python: %PY_EXE%
    echo [2/2] Đang mở trình duyệt tại http://localhost:8080 ...
    echo.
    echo (Nhấn Ctrl+C trong cửa sổ này nếu muốn dừng máy chủ)
    echo.
    %PY_EXE% run_server.py
) else (
    echo [Thông báo] Không tìm thấy Python trong hệ thống.
    echo Đang mở trực tiếp trang web index.html vào trình duyệt mặc định...
    start "" index.html
)
pause
