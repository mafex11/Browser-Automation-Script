@echo off
echo Starting Chrome with remote debugging...
echo.
echo After Chrome opens, run connect_to_chrome.py to connect to it.
echo.

REM Try to find Chrome in common locations
set "CHROME_PATH="

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if "%CHROME_PATH%"=="" (
    echo Chrome not found in common locations.
    echo Please modify this batch file to point to your Chrome installation.
    pause
    exit /b 1
)

echo Starting Chrome with remote debugging port 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222

echo.
echo Chrome started with remote debugging enabled.
echo Now you can run connect_to_chrome.py to connect to it.
echo.
pause 