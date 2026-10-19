@echo off
chcp 65001 >nul
title Stella Sora Việt Hóa - Trình Cài Đặt 1-Chạm
cd /d "%~dp0"
echo =======================================================
echo     STELLA SORA VIỆT HÓA - TRÌNH CÀI ĐẶT 1-CHẠM
echo =======================================================
echo.
python launcher_pc.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Khởi động launcher gặp lỗi hoặc đã kết thúc.
    pause
)
