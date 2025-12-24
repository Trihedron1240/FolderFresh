# Rename FolderFreshLite to FolderFresh
# Run this script from the FolderFresh-development folder

$basePath = $PSScriptRoot
$sourcePath = Join-Path $basePath "FolderFreshLite"

Write-Host "Renaming FolderFreshLite to FolderFresh..." -ForegroundColor Cyan

# Step 1: Update all source files (excluding obj and bin)
Write-Host "Updating namespace references in source files..." -ForegroundColor Yellow

$files = Get-ChildItem -Path $sourcePath -Include "*.cs","*.xaml" -Recurse |
    Where-Object { $_.FullName -notlike "*\obj\*" -and $_.FullName -notlike "*\bin\*" }

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match "FolderFreshLite") {
        $newContent = $content -replace "FolderFreshLite", "FolderFresh"
        Set-Content $file.FullName -Value $newContent -NoNewline
        Write-Host "  Updated: $($file.Name)" -ForegroundColor Gray
    }
}

# Step 2: Rename csproj if not already done
$oldCsproj = Join-Path $sourcePath "FolderFreshLite.csproj"
$newCsproj = Join-Path $sourcePath "FolderFresh.csproj"
if (Test-Path $oldCsproj) {
    Rename-Item $oldCsproj "FolderFresh.csproj"
    Write-Host "  Renamed: FolderFreshLite.csproj -> FolderFresh.csproj" -ForegroundColor Gray
}

# Step 3: Update solution file
$slnFile = Join-Path $basePath "FolderFreshLite.sln"
$newSlnFile = Join-Path $basePath "FolderFresh.sln"
if (Test-Path $slnFile) {
    $slnContent = Get-Content $slnFile -Raw
    $slnContent = $slnContent -replace "FolderFreshLite", "FolderFresh"
    Set-Content $slnFile -Value $slnContent -NoNewline
    Rename-Item $slnFile "FolderFresh.sln"
    Write-Host "  Updated and renamed solution file" -ForegroundColor Gray
} elseif (Test-Path $newSlnFile) {
    $slnContent = Get-Content $newSlnFile -Raw
    $slnContent = $slnContent -replace "FolderFreshLite", "FolderFresh"
    Set-Content $newSlnFile -Value $slnContent -NoNewline
    Write-Host "  Updated solution file" -ForegroundColor Gray
}

# Step 4: Delete obj and bin folders (they'll be regenerated)
Write-Host "Cleaning build folders..." -ForegroundColor Yellow
$objPath = Join-Path $sourcePath "obj"
$binPath = Join-Path $sourcePath "bin"
if (Test-Path $objPath) { Remove-Item $objPath -Recurse -Force; Write-Host "  Deleted: obj/" -ForegroundColor Gray }
if (Test-Path $binPath) { Remove-Item $binPath -Recurse -Force; Write-Host "  Deleted: bin/" -ForegroundColor Gray }

# Step 5: Rename folder
Write-Host "Renaming folder..." -ForegroundColor Yellow
$newFolderPath = Join-Path $basePath "FolderFresh"
if (Test-Path $sourcePath) {
    try {
        Rename-Item $sourcePath "FolderFresh"
        Write-Host "  Renamed: FolderFreshLite/ -> FolderFresh/" -ForegroundColor Green
    } catch {
        Write-Host "  Could not rename folder - it may be in use. Please close all programs using it and rename manually." -ForegroundColor Red
        Write-Host "  Manual rename: FolderFreshLite -> FolderFresh" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done! Run 'dotnet build' to verify everything works." -ForegroundColor Green
