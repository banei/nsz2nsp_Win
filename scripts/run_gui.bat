@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0.."

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

python -c "import nsz_converter" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    python -m pip install -e .
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

python -c "import importlib.util; exit(0 if importlib.util.find_spec('nsz') else 1)" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到 nsz，转换功能不可用
    echo 请运行: python -m pip install nsz
    echo.
)

python -m nsz_converter gui
