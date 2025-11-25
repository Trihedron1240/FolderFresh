$ErrorActionPreference = "Stop"

try {
    Write-Host "Cleaning previous build folders..."
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist")  { Remove-Item "dist"  -Recurse -Force }

    Write-Host "Checking PyInstaller installation..."
    python -m pip show pyinstaller > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller not found. Installing..."
        python -m pip install pyinstaller
    }

    Write-Host "Building FolderFresh.exe..."
    python -m PyInstaller --onefile --windowed --name FolderFresh src\main.py

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build completed successfully!"
    }
    else {
        Write-Host "ERROR: PyInstaller returned code $LASTEXITCODE"
    }

} catch {
    Write-Host "`n----- ERROR DETAILS -----"
    Write-Host $_.Exception.Message
    $_ | Out-File -Encoding UTF8 "build_error.txt"
    Write-Host "A full error log was saved to build_error.txt"
}

Write-Host "`nPress ENTER to exit..."
Read-Host
