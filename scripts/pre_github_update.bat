@echo off
REM GitHub更新前の品質チェックとバージョン更新スクリプト
REM PostgreSQL MCP Server Pre-GitHub Update Script

echo ================================================
echo   PostgreSQL MCP Server - Pre-GitHub Update
echo ================================================

setlocal enabledelayedexpansion

REM スクリプトのディレクトリを取得
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM プロジェクトルートに移動
cd /d "%PROJECT_ROOT%"

echo [INFO] プロジェクトディレクトリ: %CD%
echo.

REM ステップ1: コード品質チェック
echo ================================================
echo   ステップ1: コード品質チェック
echo ================================================

echo [INFO] 1. Blackによるコードフォーマットチェック...
uv run black --check src/ test/ scripts/
if %errorlevel% neq 0 (
    echo [WARNING] Blackフォーマットエラーがあります
    echo [INFO] 自動フォーマットを実行します...
    uv run black src/ test/ scripts/
    echo [SUCCESS] 自動フォーマット完了
) else (
    echo [SUCCESS] Blackフォーマットチェック完了
)

echo.

echo [INFO] 2. Flake8によるリンター実行...
uv run flake8 src/ test/ scripts/
if %errorlevel% neq 0 (
    echo [ERROR] Flake8リンターエラーがあります
    echo [INFO] エラーを修正してください
    set "LINT_ERRORS=1"
) else (
    echo [SUCCESS] Flake8リンターチェック完了
)

echo.

echo [INFO] 3. MyPyによる型チェック...
uv run mypy src/
if %errorlevel% neq 0 (
    echo [ERROR] MyPy型チェックエラーがあります
    echo [INFO] エラーを修正してください
    set "TYPE_ERRORS=1"
) else (
    echo [SUCCESS] MyPy型チェック完了
)

echo.

echo [INFO] 4. Banditによるセキュリティチェック...
uv run bandit -r src/ -f txt
if %errorlevel% neq 0 (
    echo [WARNING] Banditセキュリティ警告があります
    echo [INFO] 警告内容を確認してください
) else (
    echo [SUCCESS] Banditセキュリティチェック完了
)

echo.

echo [INFO] 5. テスト実行...
uv run python -m pytest test/ -v --tb=short --cov=src --cov-report=term-missing
if %errorlevel% neq 0 (
    echo [ERROR] テストが失敗しました
    echo [INFO] テストを修正してください
    set "TEST_ERRORS=1"
) else (
    echo [SUCCESS] テスト完了
)

echo.

REM エラーがある場合は確認
if defined LINT_ERRORS (
    echo [ERROR] Flake8リンターエラーがあります。修正してから続行してください。
    goto :error_exit
)

if defined TYPE_ERRORS (
    echo [ERROR] MyPy型チェックエラーがあります。修正してから続行してください。
    goto :error_exit
)

if defined TEST_ERRORS (
    echo [ERROR] テストエラーがあります。修正してから続行してください。
    goto :error_exit
)

echo [SUCCESS] すべてのコード品質チェックが完了しました
echo.

REM ステップ2: バージョン更新
echo ================================================
echo   ステップ2: バージョン更新
echo ================================================

echo [INFO] 現在のバージョンを確認...
python scripts\update_version.py --current

echo.
echo [INFO] バージョン更新を実行します...
echo [INFO] パッチバージョンをインクリメントします（例: 1.1.1 → 1.1.2）
python scripts\update_version.py --patch --auto-confirm

echo.
echo [SUCCESS] バージョン更新が完了しました

REM 最終確認
echo ================================================
echo   最終確認
echo ================================================

echo [INFO] 更新後のバージョンを確認...
python scripts\update_version.py --current

echo.
echo [INFO] Gitステータスを確認...
git status

echo.
echo ================================================
echo   [SUCCESS] すべての事前チェックが完了しました
echo ================================================
echo [INFO] 以下のコマンドでGitHubにプッシュできます:
echo        git add .
echo        git commit -m "バージョン更新と品質チェック完了"
echo        git push origin main
echo ================================================

exit /b 0

:error_exit
echo.
echo ================================================
echo   [ERROR] コード品質チェックでエラーがあります
echo ================================================
echo [INFO] エラーを修正してから再度このスクリプトを実行してください
echo [INFO] 個別のチェックを実行する場合は:
echo        - フォーマット: uv run black src/ test/ scripts/
echo        - リンター: uv run flake8 src/ test/ scripts/
echo        - 型チェック: uv run mypy src/
echo        - テスト: uv run python -m pytest test/
echo ================================================
exit /b 1
