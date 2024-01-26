# check to see if the virtual environment exists
if (Test-Path ./venvs/main) {
    Write-Output "venv exists"
} else {
    Write-Output "venv does not exist"
    python -m venv ./venvs/main
}

./venvs/main/Scripts/activate
pip install -e .
.\unittest_coverage.ps1 donotopenhtml