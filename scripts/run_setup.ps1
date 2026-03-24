# Z Ledger: Create PostgreSQL user and database
# Run this once. You'll be prompted for the postgres superuser password.

$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
$script = Join-Path $PSScriptRoot "setup_all.sql"
$projectRoot = Split-Path $PSScriptRoot -Parent

if (-not (Test-Path $psql)) {
    Write-Error "psql not found at $psql. Adjust path if using a different PostgreSQL version."
    exit 1
}

Write-Host "Creating user bnobody and database z_ledger..."
Set-Location $projectRoot
& $psql -U postgres -f $script
if ($LASTEXITCODE -eq 0) {
    Write-Host "Done. Set DATABASE_URL and run tests:"
    Write-Host '  $env:DATABASE_URL="postgresql://bnobody:beahhal@localhost:5432/z_ledger"'
    Write-Host '  python -m pytest tests/test_concurrency.py -v -s'
} else {
    Write-Host "Setup failed. Run manually: & `"$psql`" -U postgres -f `"$script`""
}
