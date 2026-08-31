@echo off
chcp 936 > nul
cls
echo ==========================================
echo  说唱音乐行业双周报自动化工具
echo ==========================================
echo.

REM 检查是否在 WSL 网络路径下运行
set "CURRENT_DIR=%cd%"
echo %CURRENT_DIR% | findstr /I "\\wsl.localhost\" > nul
if %errorlevel% equ 0 (
    echo [错误] 检测到当前目录位于 WSL 子系统路径中。
    echo        请把项目复制到 Windows 本地目录，例如 D:\rap-report-tool
    pause
    exit /b 1
)

echo [信息] 当前目录：%CURRENT_DIR%

REM 检查 Python
where python > nul 2> nul
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未找到 Python。
    echo.
    echo 本工具需要 Python 3.11 或更高版本才能运行。
    echo.
    echo 请按以下步骤安装：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载 Python 3.11 或更高版本
    echo   3. 安装时务必勾选 Add Python to PATH
    echo   4. 安装完成后重新双击本文件
    echo.
    pause
    exit /b 1
)

echo [信息] Python 版本：
python --version
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [信息] 正在创建虚拟环境，请稍候...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败。
        pause
        exit /b 1
    )
    echo [信息] 虚拟环境创建完成。
) else (
    echo [信息] 虚拟环境已存在。
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败。
    pause
    exit /b 1
)

REM 安装/更新依赖
echo [信息] 正在检查并安装依赖，请稍候...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络连接。
    pause
    exit /b 1
)
echo [信息] 依赖检查完成。
echo.

REM 运行主程序
echo [信息] 正在生成报告...
python run.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序运行失败，错误码：%errorlevel%
    echo        请截图上述错误信息并反馈给开发者。
    pause
    exit /b 1
)

echo.
echo [信息] 报告生成完成！
echo [信息] 请在 output 文件夹中查看生成的报告文件。
echo.
echo 按任意键退出...
pause > nul
