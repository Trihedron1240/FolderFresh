# ---------------------------
#  FolderFresh Build Script
# ---------------------------

# 1) Set the new version here:
$version = "1.2.1"

# 2) Write version into VERSION file
Set-Content -Path "src/folderfresh/VERSION" -Value $version

# 3) Clean previous builds
Write-Host "Cleaning build folders..."
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist")  { Remove-Item "dist"  -Recurse -Force }

# 4) Ensure PyInstaller installed
Write-Host "Checking PyInstaller..."
python -m pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    python -m pip install pyinstaller
}

# 5) Build EXE
Write-Host "Building FolderFresh $version..."
pyinstaller --onefile --windowed --clean --noupx `
  --add-data "src/folderfresh/VERSION;folderfresh" `
  --name FolderFresh src/main.py


if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed."
    exit 1
}

Write-Host "Build completed successfully!"
