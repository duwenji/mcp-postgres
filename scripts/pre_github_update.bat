@echo off
REM GitHub�X�V�O�̕i���`�F�b�N�ƃo�[�W�����X�V�X�N���v�g
REM PostgreSQL MCP Server Pre-GitHub Update Script

echo ================================================
echo   PostgreSQL MCP Server - Pre-GitHub Update
echo ================================================

setlocal enabledelayedexpansion

REM �X�N���v�g�̃f�B���N�g�����擾
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM �v���W�F�N�g���[�g�Ɉړ�
cd /d "%PROJECT_ROOT%"

echo [INFO] �v���W�F�N�g�f�B���N�g��: %CD%
echo.

REM �X�e�b�v1: �R�[�h�i���`�F�b�N
echo ================================================
echo   �X�e�b�v1: �R�[�h�i���`�F�b�N
echo ================================================

echo [INFO] 1. Black�ɂ��R�[�h�t�H�[�}�b�g�`�F�b�N...
uv run black --check src/ test/ scripts/
if %errorlevel% neq 0 (
    echo [WARNING] Black�t�H�[�}�b�g�G���[������܂�
    echo [INFO] �����t�H�[�}�b�g�����s���܂�...
    uv run black src/ test/ scripts/
    echo [SUCCESS] �����t�H�[�}�b�g����
) else (
    echo [SUCCESS] Black�t�H�[�}�b�g�`�F�b�N����
)

echo.

echo [INFO] 2. Flake8�ɂ�郊���^�[���s...
uv run flake8 src/ test/ scripts/
if %errorlevel% neq 0 (
    echo [ERROR] Flake8�����^�[�G���[������܂�
    echo [INFO] �G���[���C�����Ă�������
    set "LINT_ERRORS=1"
) else (
    echo [SUCCESS] Flake8�����^�[�`�F�b�N����
)

echo.

echo [INFO] 3. MyPy�ɂ��^�`�F�b�N...
uv run mypy src/
if %errorlevel% neq 0 (
    echo [ERROR] MyPy�^�`�F�b�N�G���[������܂�
    echo [INFO] �G���[���C�����Ă�������
    set "TYPE_ERRORS=1"
) else (
    echo [SUCCESS] MyPy�^�`�F�b�N����
)

echo.

echo [INFO] 4. Bandit�ɂ��Z�L�����e�B�`�F�b�N...
uv run bandit -r src/ -f txt
if %errorlevel% neq 0 (
    echo [WARNING] Bandit�Z�L�����e�B�x��������܂�
    echo [INFO] �x�����e���m�F���Ă�������
) else (
    echo [SUCCESS] Bandit�Z�L�����e�B�`�F�b�N����
)

echo.

echo [INFO] 5. �e�X�g���s...
uv run python -m pytest test/ -v --tb=short --cov=src --cov-report=term-missing
if %errorlevel% neq 0 (
    echo [ERROR] �e�X�g�����s���܂���
    echo [INFO] �e�X�g���C�����Ă�������
    set "TEST_ERRORS=1"
) else (
    echo [SUCCESS] �e�X�g����
)

echo.

REM �G���[������ꍇ�͊m�F
if defined LINT_ERRORS (
    echo [ERROR] Flake8�����^�[�G���[������܂��B�C�����Ă��瑱�s���Ă��������B
    goto :error_exit
)

if defined TYPE_ERRORS (
    echo [ERROR] MyPy�^�`�F�b�N�G���[������܂��B�C�����Ă��瑱�s���Ă��������B
    goto :error_exit
)

if defined TEST_ERRORS (
    echo [ERROR] �e�X�g�G���[������܂��B�C�����Ă��瑱�s���Ă��������B
    goto :error_exit
)

echo [SUCCESS] ���ׂẴR�[�h�i���`�F�b�N���������܂���
echo.

REM �X�e�b�v2: �o�[�W�����X�V
echo ================================================
echo   �X�e�b�v2: �o�[�W�����X�V
echo ================================================

echo [INFO] ���݂̃o�[�W�������m�F...
python scripts\update_version.py --current

echo.
echo [INFO] �o�[�W�����X�V�����s���܂�...
echo [INFO] �p�b�`�o�[�W�������C���N�������g���܂��i��: 1.1.1 �� 1.1.2�j
python scripts\update_version.py --patch --auto-confirm

echo.
echo [SUCCESS] �o�[�W�����X�V���������܂���

REM �ŏI�m�F
echo ================================================
echo   �ŏI�m�F
echo ================================================

echo [INFO] �X�V��̃o�[�W�������m�F...
python scripts\update_version.py --current

echo.
echo [INFO] Git�X�e�[�^�X���m�F...
git status

echo.
echo ================================================
echo   [SUCCESS] ���ׂĂ̎��O�`�F�b�N���������܂���
echo ================================================
echo [INFO] �ȉ��̃R�}���h��GitHub�Ƀv�b�V���ł��܂�:
echo        git add .
echo        git commit -m "�o�[�W�����X�V�ƕi���`�F�b�N����"
echo        git push origin main
echo ================================================

exit /b 0

:error_exit
echo.
echo ================================================
echo   [ERROR] �R�[�h�i���`�F�b�N�ŃG���[������܂�
echo ================================================
echo [INFO] �G���[���C�����Ă���ēx���̃X�N���v�g�����s���Ă�������
echo [INFO] �ʂ̃`�F�b�N�����s����ꍇ��:
echo        - �t�H�[�}�b�g: uv run black src/ test/ scripts/
echo        - �����^�[: uv run flake8 src/ test/ scripts/
echo        - �^�`�F�b�N: uv run mypy src/
echo        - �e�X�g: uv run python -m pytest test/
echo ================================================
exit /b 1
