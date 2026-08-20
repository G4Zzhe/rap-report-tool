@echo off
chcp 65001 > nul
echo ==========================================
echo  说唱音乐行业双周报自动化工具（无 AI 模式）
echo ==========================================
echo.

echo [调试] 当前目录：%cd%
pause

REM 检查 Python
where python > nul 2> nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 python，请安装 Python 3.10 或更高版本。
    echo        下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [调试] Python 版本：
python --version
pause

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo 正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败。
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败。
    pause
    exit /b 1
)

REM 安装/更新依赖
echo 正在检查依赖...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败。
    pause
    exit /b 1
)

REM 运行主程序（禁用 AI）
echo 正在运行（无 AI 文案生成）...
python run.py --no-ai
if %errorlevel% neq 0 (
    echo [错误] 程序运行失败，错误码：%errorlevel%
    pause
    exit /b 1
)

echo.
echo 运行结束，按任意键退出。
pause > nul
