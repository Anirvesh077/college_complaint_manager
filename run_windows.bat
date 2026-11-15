@echo off
title College Complaint Manager
cd /d "%~dp0"
py app.py
if errorlevel 1 (
  echo.
  echo Python could not start the app. Check the README troubleshooting section.
  pause
)
