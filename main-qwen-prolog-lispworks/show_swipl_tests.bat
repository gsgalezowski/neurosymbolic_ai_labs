@echo off
cd /d "%~dp0"
swipl --version
echo.
swipl -q -g "run_tests,halt" -s test_guard.pl
echo.
if errorlevel 1 (
  echo RESULT: symbolic guard tests FAILED.
) else (
  echo RESULT: 3 symbolic guard tests passed.
)
