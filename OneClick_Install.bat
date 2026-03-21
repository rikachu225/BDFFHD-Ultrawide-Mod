@echo off
setlocal enabledelayedexpansion
title BDFFHD Ultrawide Mod - One-Click Installer
color 0B

echo.
echo   ╔═══════════════════════════════════════════════════════════╗
echo   ║   BRAVELY DEFAULT: FLYING FAIRY HD - Ultrawide Mod       ║
echo   ║   One-Click Installer                                    ║
echo   ║                                                          ║
echo   ║   This will install BepInEx + the Ultrawide Mod          ║
echo   ║   automatically into your game folder.                   ║
echo   ╚═══════════════════════════════════════════════════════════╝
echo.

:: ─── Find Game Directory ────────────────────────────────────────
set "GAME_DIR="

:: Check common Steam library locations across drives
for %%D in (C D E F G H) do (
    if exist "%%D:\SteamLibrary\steamapps\common\BDFFHD\BDFFHD.exe" (
        set "GAME_DIR=%%D:\SteamLibrary\steamapps\common\BDFFHD"
    )
    if exist "%%D:\Program Files (x86)\Steam\steamapps\common\BDFFHD\BDFFHD.exe" (
        set "GAME_DIR=%%D:\Program Files (x86)\Steam\steamapps\common\BDFFHD"
    )
    if exist "%%D:\Program Files\Steam\steamapps\common\BDFFHD\BDFFHD.exe" (
        set "GAME_DIR=%%D:\Program Files\Steam\steamapps\common\BDFFHD"
    )
    if exist "%%D:\Games\Steam\steamapps\common\BDFFHD\BDFFHD.exe" (
        set "GAME_DIR=%%D:\Games\Steam\steamapps\common\BDFFHD"
    )
    if exist "%%D:\Steam\steamapps\common\BDFFHD\BDFFHD.exe" (
        set "GAME_DIR=%%D:\Steam\steamapps\common\BDFFHD"
    )
)

if defined GAME_DIR (
    echo   [FOUND] Game directory: !GAME_DIR!
    echo.
) else (
    echo   [!] Game not found automatically.
    echo.
    echo   Please enter the full path to your BDFFHD game folder.
    echo   Example: D:\SteamLibrary\steamapps\common\BDFFHD
    echo.
    set /p "GAME_DIR=  Path: "
    set "GAME_DIR=!GAME_DIR:"=!"

    if not exist "!GAME_DIR!\BDFFHD.exe" (
        echo.
        echo   [ERROR] BDFFHD.exe not found at that location.
        echo          Make sure you entered the correct game folder.
        echo.
        pause
        exit /b 1
    )
)

:: ─── Check if BepInEx is already installed ──────────────────────
if exist "!GAME_DIR!\BepInEx\core\BepInEx.Core.dll" (
    echo   [OK] BepInEx is already installed.
    goto :install_mod
)

:: ─── Download BepInEx ───────────────────────────────────────────
echo   [1/3] Downloading BepInEx 6 (Unity IL2CPP, win-x64)...
echo.

:: Check for curl (built into Windows 10+)
where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] curl not found. You need Windows 10 or later.
    echo          Or download BepInEx manually from:
    echo          https://builds.bepinex.dev/projects/bepinex_be
    pause
    exit /b 1
)

:: Download latest BepInEx 6 BE for Unity IL2CPP
set "BEPINEX_URL=https://github.com/BepInEx/BepInEx/releases/download/v6.0.0-pre.2/BepInEx-Unity.IL2CPP-win-x64-6.0.0-pre.2.zip"
set "BEPINEX_ZIP=%TEMP%\bepinex_il2cpp.zip"

curl -L -o "!BEPINEX_ZIP!" "!BEPINEX_URL!" 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Download failed. Check your internet connection.
    echo          You can also download BepInEx manually from:
    echo          https://github.com/BepInEx/BepInEx/releases
    echo          Get: BepInEx-Unity.IL2CPP-win-x64
    pause
    exit /b 1
)

echo.
echo   [2/3] Extracting BepInEx to game folder...

:: Extract using PowerShell (available on all modern Windows)
powershell -NoProfile -Command "Expand-Archive -Path '!BEPINEX_ZIP!' -DestinationPath '!GAME_DIR!' -Force" 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Extraction failed.
    echo          Try extracting manually: !BEPINEX_ZIP!
    echo          Into: !GAME_DIR!
    pause
    exit /b 1
)

:: Clean up downloaded zip
del "!BEPINEX_ZIP!" 2>nul

echo   [OK] BepInEx installed.
echo.

:: ─── First-run: BepInEx needs to generate files ────────────────
echo   [NOTE] BepInEx needs one game launch to initialize.
echo          The game will start and may close automatically.
echo          This is normal — wait for it to finish.
echo.

:: Create plugins dir if it doesn't exist yet
if not exist "!GAME_DIR!\BepInEx\plugins" (
    mkdir "!GAME_DIR!\BepInEx\plugins"
)

:: ─── Install the Ultrawide Mod ──────────────────────────────────
:install_mod
echo   [3/3] Installing Ultrawide Mod...

:: Get the directory where this script lives
set "SCRIPT_DIR=%~dp0"

:: Copy mod DLL
if exist "!SCRIPT_DIR!BepInEx\plugins\BDFFHD_UltrawideMod.dll" (
    copy /y "!SCRIPT_DIR!BepInEx\plugins\BDFFHD_UltrawideMod.dll" "!GAME_DIR!\BepInEx\plugins\" >nul
    echo   [OK] BDFFHD_UltrawideMod.dll installed.
) else (
    echo   [ERROR] Could not find BDFFHD_UltrawideMod.dll
    echo          Make sure this script is in the same folder as the BepInEx folder.
    pause
    exit /b 1
)

:: ─── Done ───────────────────────────────────────────────────────
echo.
echo   ╔══════════════════════════════════════════════════════════════╗
echo   ║   INSTALLATION COMPLETE!                                    ║
echo   ║                                                             ║
echo   ║   Next steps:                                               ║
echo   ║   1. Launch the game from Steam                             ║
echo   ║   2. Close it after it starts (BepInEx will initialize)     ║
echo   ║   3. Open: BepInEx\config\com.community.bdffhd.ultrawide.cfg║
echo   ║   4. Set your monitor's Width and Height                    ║
echo   ║   5. Launch again and enjoy ultrawide!                      ║
echo   ║                                                             ║
echo   ║   To uninstall: delete BepInEx folder from game directory   ║
echo   ║   Or: Steam ^> Verify Game Files                            ║
echo   ╚══════════════════════════════════════════════════════════════╝
echo.
pause
