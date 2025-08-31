
param(
  [string]$ProjectDir = ".",
  [string]$FixturesDir = ".\fixtures"
)
Set-Location $ProjectDir
if (-not (Test-Path .\.venv)) { py -3 -m venv .venv }
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel
pip install -r requirements.txt
if (Test-Path .\db.sqlite3) { Remove-Item .\db.sqlite3 -Force }
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
if (Test-Path $FixturesDir) {
  Get-ChildItem $FixturesDir -Filter *.json | ForEach-Object {
    Write-Host "Loading $($_.FullName)"
    python manage.py loaddata $_.FullName
  }
}
Write-Host "If you need a superuser, run: python manage.py createsuperuser"
python manage.py runserver
