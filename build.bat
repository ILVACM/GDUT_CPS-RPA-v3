@echo off
rem ============================================================
rem  RPA_Workflow_v3 one-click build script (PyInstaller, onefile GUI)
rem  ------------------------------------------------------------
rem  R6/C2 (P1-9): build into temp dir, atomic publish, old exe
rem    backed up first; user data dirs under BUILD_DIR
rem    (workspace / logs / storage / temp / backup) are NEVER deleted.
rem  R6/C1 (P0-3, D5): source fingerprint (SOURCE_HASH + GIT_REV)
rem    injected into BUILD_INFO.txt via tools\make_fingerprint.py.
rem  R6/C2 (D4): mandatory test gate before packaging
rem    (unittest discover + 2 smoke scripts); --skip-tests bypasses
rem    explicitly and is recorded as TESTS_SKIPPED=1.
rem
rem  Usage:  build.bat [--build-dir <path>] [--output <path>]
rem                    [--clean] [--skip-tests]
rem    --build-dir <path>  intermediate/output dir (default: .\build\)
rem    --output <path>     extra copy target for the .exe
rem    --clean             remove intermediates AFTER success
rem    --skip-tests        bypass test gate (recorded; review needed)
rem    bare <path>         legacy compat: treated as --output
rem
rem  Prereq: conda env activated (CPS-GPES_RPA-py311) + PyInstaller.
rem  Note (R6): messages are pure ASCII on purpose - the original
rem    GBK-encoded Chinese messages were replaced to keep the script
rem    encoding-safe across editors/agents. Parameter interface and
rem    behavior contract are preserved (docs/build-guide.md sec.2).
rem ============================================================
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "SPEC_FILE=RPA_Workflow_v3.spec"
set "APP_NAME=RPA_Workflow_v3"

cd /d "%SCRIPT_DIR%"
if not exist "%SPEC_FILE%" (
    echo [ERROR] Spec file not found: %SPEC_FILE%
    echo [HINT]  Keep %SPEC_FILE% and build.bat in the same directory.
    pause
    exit /b 1
)

rem ---------- Step 0: arguments ----------
echo [Step 0] Parsing arguments

set "BUILD_DIR=%SCRIPT_DIR%build"
set "OUTPUT_EXTRA="
set "DO_CLEAN=0"
set "SKIP_TESTS=0"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--build-dir" goto :arg_build_dir
if /I "%~1"=="--output" goto :arg_output
if /I "%~1"=="--clean" goto :arg_clean
if /I "%~1"=="--skip-tests" goto :arg_skip_tests
rem bare path argument: legacy compat, treated as --output
if defined OUTPUT_EXTRA goto :arg_unknown
set "OUTPUT_EXTRA=%~1"
echo [INFO] Bare path treated as --output. Prefer: --output ^<path^>
shift
goto :parse_args

:arg_build_dir
shift
if "%~1"=="" (echo [ERROR] --build-dir requires a path& pause& exit /b 1)
set "BUILD_DIR=%~1"
shift
goto :parse_args

:arg_output
shift
if "%~1"=="" (echo [ERROR] --output requires a path& pause& exit /b 1)
set "OUTPUT_EXTRA=%~1"
shift
goto :parse_args

:arg_clean
set "DO_CLEAN=1"
shift
goto :parse_args

:arg_skip_tests
set "SKIP_TESTS=1"
shift
goto :parse_args

:arg_unknown
echo [ERROR] Unknown argument: %~1
pause
exit /b 1

:args_done

rem illegal character check (subroutine; avoids cmd pre-scan issues)
call :validate_path "!BUILD_DIR!" "BUILD_DIR"
if errorlevel 1 exit /b 1
call :validate_path "!OUTPUT_EXTRA!" "OUTPUT_EXTRA"
if errorlevel 1 exit /b 1

rem path normalization: relative -> absolute
if not "!BUILD_DIR:~0,1!"=="\" if not "!BUILD_DIR:~1,1!"==":" set "BUILD_DIR=%SCRIPT_DIR%!BUILD_DIR!"
if not "!OUTPUT_EXTRA:~0,1!"=="\" if not "!OUTPUT_EXTRA:~1,1!"==":" if defined OUTPUT_EXTRA set "OUTPUT_EXTRA=%SCRIPT_DIR%!OUTPUT_EXTRA!"

if not exist "!BUILD_DIR!\" mkdir "!BUILD_DIR!"

echo [CONFIG] Build dir   : !BUILD_DIR!
if defined OUTPUT_EXTRA (
    echo [CONFIG] Extra output: !OUTPUT_EXTRA!
) else (
    echo [CONFIG] Extra output: none
)
echo [CONFIG] Clean       : !DO_CLEAN!
echo [CONFIG] Skip tests  : !SKIP_TESTS!

rem ---------- Step 1: environment ----------
echo.
echo [Step 1] Environment check

if defined CONDA_DEFAULT_ENV (
    echo [INFO] conda env: %CONDA_DEFAULT_ENV%
) else (
    echo [ERROR] No conda env activated - CONDA_DEFAULT_ENV not set
    echo [HINT]  Run: conda activate CPS-GPES_RPA-py311
    echo [HINT]  Then re-run this build script
    pause
    exit /b 1
)

set "PYI_MODE="
where pyinstaller >nul 2>nul
if not errorlevel 1 set "PYI_MODE=exe"
if not defined PYI_MODE (
    python -m PyInstaller --version >nul 2>nul
    if not errorlevel 1 set "PYI_MODE=module"
)
if not defined PYI_MODE (
    echo [ERROR] PyInstaller not installed in current env.
    echo [HINT]  Run: pip install pyinstaller
    pause
    exit /b 1
)

set "PY_VER=unknown"
for /f "delims=" %%V in ('python --version 2^>nul') do set "PY_VER=%%V"
set "PYI_VER=unknown"
if "!PYI_MODE!"=="exe" (
    for /f "delims=" %%V in ('pyinstaller --version 2^>nul') do set "PYI_VER=%%V"
) else (
    for /f "delims=" %%V in ('python -m PyInstaller --version 2^>nul') do set "PYI_VER=%%V"
)
echo [INFO] !PY_VER! / PyInstaller !PYI_VER!

rem ---------- Step 2: test gate (R6/C2, D4=mandatory) ----------
echo.
echo [Step 2] Test gate
if "!SKIP_TESTS!"=="1" goto :gate_skipped
pushd "%SCRIPT_DIR%rpa_engine"
python -m unittest discover -s tests
if errorlevel 1 goto :gate_failed
python tools\smoke\smoke_m1m3.py > "%TEMP%\r6_smoke1.log" 2>&1
findstr /C:"SMOKE_ALL_OK" "%TEMP%\r6_smoke1.log" >nul
if errorlevel 1 goto :gate_failed
python tools\smoke\smoke_mb.py > "%TEMP%\r6_smoke2.log" 2>&1
findstr /C:"SMOKE_ALL_OK" "%TEMP%\r6_smoke2.log" >nul
if errorlevel 1 goto :gate_failed
popd
echo [INFO] Test gate PASSED (unittest + 2 smokes)
goto :gate_done

:gate_skipped
echo [WARN] Tests SKIPPED via --skip-tests (recorded in BUILD_INFO)
goto :gate_done

:gate_failed
popd
echo [ERROR] Test gate FAILED. Packaging aborted. Nothing was modified.
echo [HINT]  Fix failures first, or bypass explicitly with --skip-tests.
pause
exit /b 1

:gate_done

rem ---------- Step 3: source fingerprint (R6/C1, D5=dual) ----------
echo.
echo [Step 3] Source fingerprint
set "FP_FILE=!BUILD_DIR!\_fingerprint.tmp"
python tools\make_fingerprint.py > "!FP_FILE!" 2>nul
if errorlevel 1 (
    echo [WARN] Fingerprint script failed; SOURCE_HASH=N/A
    > "!FP_FILE!" echo SOURCE_HASH=N/A
)
set "SOURCE_HASH=N/A"
for /f "tokens=1,* delims==" %%A in ('findstr /B "SOURCE_HASH=" "!FP_FILE!"') do set "SOURCE_HASH=%%B"
set "GIT_REV=N/A"
for /f "tokens=1,* delims==" %%A in ('findstr /B "GIT_REV=" "!FP_FILE!"') do set "GIT_REV=%%B"
del /q "!FP_FILE!" 2>nul
echo [INFO] SOURCE_HASH=!SOURCE_HASH!
echo [INFO] GIT_REV=!GIT_REV!

rem ---------- Step 4: build into TEMP dir (user data untouched) ----------
echo.
echo [Step 4] PyInstaller build (temp dir; single-file GUI, be patient)
set "TMP_ROOT=!BUILD_DIR!\_build_tmp"
if exist "!TMP_ROOT!" rmdir /s /q "!TMP_ROOT!"
mkdir "!TMP_ROOT!"
set "PYI_WORK=!TMP_ROOT!\work"
set "PYI_DIST=!TMP_ROOT!\dist"
echo ============================================
if "!PYI_MODE!"=="exe" (
    pyinstaller --noconfirm --log-level=INFO --workpath "!PYI_WORK!" --distpath "!PYI_DIST!" "%SPEC_FILE%"
) else (
    python -m PyInstaller --noconfirm --log-level=INFO --workpath "!PYI_WORK!" --distpath "!PYI_DIST!" "%SPEC_FILE%"
)
set "PYI_EXITCODE=!ERRORLEVEL!"
echo ============================================
echo  [BUILD] PyInstaller exit code: !PYI_EXITCODE!
if !PYI_EXITCODE! neq 0 goto :build_failed
set "EXE_SRC=!PYI_DIST!\%APP_NAME%.exe"
if not exist "!EXE_SRC!" goto :build_failed
echo [INFO] Build succeeded

rem ---------- Step 5: atomic publish (backup old exe first) ----------
echo.
echo [Step 5] Publish exe (backup old, then replace)
if not exist "!BUILD_DIR!\backup\" mkdir "!BUILD_DIR!\backup"
if exist "!BUILD_DIR!\%APP_NAME%.exe" (
    set "STAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
    set "STAMP=!STAMP: =0!"
    move /Y "!BUILD_DIR!\%APP_NAME%.exe" "!BUILD_DIR!\backup\%APP_NAME%_!STAMP!.exe" >nul
    echo [INFO] Old exe backed up: backup\%APP_NAME%_!STAMP!.exe
)
copy /Y "!EXE_SRC!" "!BUILD_DIR!\%APP_NAME%.exe" >nul
set "EXE_FINAL=!BUILD_DIR!\%APP_NAME%.exe"

if defined OUTPUT_EXTRA (
    if exist "!OUTPUT_EXTRA!\" (
        copy /Y "!EXE_SRC!" "!OUTPUT_EXTRA!\%APP_NAME%.exe" >nul
        set "EXE_EXTRA=!OUTPUT_EXTRA!\%APP_NAME%.exe"
    ) else (
        for %%I in ("!OUTPUT_EXTRA!") do set "EXE_EXTRA_DIR=%%~dpI"
        if not exist "!EXE_EXTRA_DIR!" mkdir "!EXE_EXTRA_DIR!"
        copy /Y "!EXE_SRC!" "!OUTPUT_EXTRA!" >nul
        set "EXE_EXTRA=!OUTPUT_EXTRA!"
    )
    echo [INFO] Extra copy: !EXE_EXTRA!
)

for %%F in ("!EXE_FINAL!") do set "EXE_SIZE=%%~zF"
set /a EXE_MB10=EXE_SIZE/104857
set /a EXE_MB=EXE_MB10/10
set /a EXE_MB_FRAC=EXE_MB10%%10

set "BUILD_TIME=%date% %time%"
(
    echo ================================================
    echo  RPA_Workflow_v3 BUILD INFO
    echo ================================================
    echo BUILD_TIME      : !BUILD_TIME!
    echo EXE_PATH        : !EXE_FINAL!
    if defined OUTPUT_EXTRA echo EXTRA_COPY      : !EXE_EXTRA!
    echo CONDA_ENV       : %CONDA_DEFAULT_ENV%
    echo PYTHON          : !PY_VER!
    echo PYINSTALLER     : !PYI_VER!
    echo SOURCE_HASH     : !SOURCE_HASH!
    echo GIT_REV         : !GIT_REV!
    echo TESTS_SKIPPED   : !SKIP_TESTS!
    echo ================================================
) > "!BUILD_DIR!\BUILD_INFO.txt"
echo [INFO] BUILD_INFO written: !BUILD_DIR!\BUILD_INFO.txt

echo.
echo [SUCCESS] Build complete
echo [OUTPUT] exe     : !EXE_FINAL!
if defined OUTPUT_EXTRA echo [OUTPUT] extra  : !EXE_EXTRA!
echo [SIZE]   size    : !EXE_MB!.!EXE_MB_FRAC! MB

rem ---------- Step 6: cleanup intermediates ----------
echo.
echo [Step 6] Cleanup
rem temp build root is always removed after success
if exist "!TMP_ROOT!" rmdir /s /q "!TMP_ROOT!"
if "!DO_CLEAN!"=="1" (
    if not exist "!EXE_FINAL!" (
        echo [ERROR] Post-check failed: !EXE_FINAL! missing, cleanup aborted
        pause
        exit /b 1
    )
    rem legacy intermediate dirs (pre-R6 builds put them in BUILD_DIR)
    if exist "!BUILD_DIR!\work" rmdir /s /q "!BUILD_DIR!\work"
    if exist "!BUILD_DIR!\spec" rmdir /s /q "!BUILD_DIR!\spec"
    if exist "!BUILD_DIR!\dist" rmdir /s /q "!BUILD_DIR!\dist"
    del /q "!BUILD_DIR!\*.toc" 2>nul
    del /q "!BUILD_DIR!\*.waf*" 2>nul
    if exist "!BUILD_DIR!\__pycache__" rmdir /s /q "!BUILD_DIR!\__pycache__"
    echo [CLEAN] Intermediates removed.
)
echo [INFO] NEVER touched by this script: workspace\ logs\ storage\ temp\ backup\ and the published exe

echo.
echo All steps finished.
pause
exit /b 0

:build_failed
echo.
echo [ERROR] PyInstaller build FAILED. Old exe (if any) is UNTOUCHED.
if exist "!TMP_ROOT!" rmdir /s /q "!TMP_ROOT!"
pause
exit /b 1

rem ============================================================
rem  Subroutine: validate path against cmd special characters
rem  %~1 = value, %~2 = name; errorlevel 0 = ok, 1 = illegal
rem ============================================================
:validate_path
setlocal EnableDelayedExpansion
set "VP_VAL=%~1"
set "VP_NAME=%~2"

if not defined VP_VAL endlocal & exit /b 0

set "VP_CHARS=&|<>^"""
set "VP_LEN=0"
:vp_count_len
if "!VP_VAL:~%VP_LEN%,1!"=="" goto :vp_check_loop
set /a VP_LEN+=1
goto :vp_count_len

:vp_check_loop
set "VP_IDX=0"
:vp_char_iter
if %VP_IDX% geq %VP_LEN% endlocal & exit /b 0
set "VP_C=!VP_VAL:~%VP_IDX%,1!"
set "VP_SIX=0"
:vp_special_iter
if "!VP_CHARS:~%VP_SIX%,1!"=="" (
    set /a VP_IDX+=1
    goto :vp_char_iter
)
if "!VP_C!"=="!VP_CHARS:~%VP_SIX%,1!" goto :vp_found_bad
set /a VP_SIX+=1
goto :vp_special_iter

:vp_found_bad
echo [ERROR] %VP_NAME% contains illegal characters: ^& ^| ^< ^> ^^ or quotes
endlocal & exit /b 1
