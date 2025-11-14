@echo off

REM 切换到脚本所在目录
cd /d %~dp0

echo 正在安装依赖项...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 依赖安装失败！
    pause
    exit /b 1
)

echo 正在打包应用程序...
python -m PyInstaller love_story.spec

if %errorlevel% neq 0 (
    echo 打包失败！
    pause
    exit /b 1
)

echo 打包完成！可执行文件位于 dist/ 目录下
pause