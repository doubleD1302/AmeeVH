@echo off
chcp 65001 >nul
title Stella Sora - Trạm Dịch Thuật Cốt Truyện

echo ======================================================================
echo    🌟 STELLA SORA — TRẠM DỊCH THUẬT CỐT TRUYỆN (GAMEPLAY STUDIO)
echo ======================================================================
echo.
echo Đang khởi động Server đồng bộ với Google Sheets...
echo.

start "" "http://localhost:8088"
python server.py

pause
