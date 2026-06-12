@echo off
REM ============================================================
REM NUKSAMS 一鍵啟動（雙擊我！）
REM 自動完成：環境檢查 -> 安裝套件 -> 初始化資料庫 -> 啟動前後端
REM 細節在 scripts\start.ps1，問題排查見 docs\DEVELOPMENT.md
REM ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start.ps1"
pause
