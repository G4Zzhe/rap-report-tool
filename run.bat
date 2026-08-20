@echo off
chcp 65001 > nul
echo ==========================================
echo  说唱音乐行业双周报自动化工具
echo ==========================================
echo.

REM 检查 Python
where python > nul 2> nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 python，请安装 Python 3.10 或更高版本。
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat

REM 安装/更新依赖
echo 正在检查依赖...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败。
    pause
    exit /b 1
)

REM 运行主程序
echo 正在运行...
python run.py %*

echo.
echo 运行结束，按任意键退出。
pause > nul
