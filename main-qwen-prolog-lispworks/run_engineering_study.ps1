$ErrorActionPreference = "Stop"
$env:PYTHONPATH = $PSScriptRoot
python -m engineering_study.reproduce @args
