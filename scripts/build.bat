@echo off
setlocal

cd /d "%~dp0.."

echo 安装打包依赖...
python -m pip install -e ".[dev]"
if errorlevel 1 exit /b 1

echo 开始打包...
python -m PyInstaller build\nsz-converter.spec --noconfirm --distpath dist --workpath build\pyinstaller
if errorlevel 1 exit /b 1

echo.
echo 打包完成: dist\NSZ-Converter.exe
echo 可直接双击运行，无需 python 命令。
