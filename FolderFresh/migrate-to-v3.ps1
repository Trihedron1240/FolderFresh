# FolderFresh v2.0 to v3.0 Migration Script
# This script helps transition your repo from Python/PySide6 to C#/.NET 9

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath,  # Path to your FolderFresh git repository

    [Parameter(Mandatory=$true)]
    [string]$SourcePath  # Path to FolderFreshLite folder (this folder)
)

$ErrorActionPreference = "Stop"

Write-Host "FolderFresh v3.0 Migration Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Validate paths
if (-not (Test-Path $RepoPath)) {
    Write-Error "Repository path does not exist: $RepoPath"
    exit 1
}

if (-not (Test-Path "$RepoPath\.git")) {
    Write-Error "Not a git repository: $RepoPath"
    exit 1
}

if (-not (Test-Path $SourcePath)) {
    Write-Error "Source path does not exist: $SourcePath"
    exit 1
}

Write-Host "Repository: $RepoPath" -ForegroundColor Yellow
Write-Host "Source: $SourcePath" -ForegroundColor Yellow
Write-Host ""

# Step 1: Create archive branch
Write-Host "[1/5] Creating v2.0-archive branch..." -ForegroundColor Green
Push-Location $RepoPath
try {
    git checkout -b v2.0-archive 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Branch v2.0-archive may already exist, continuing..." -ForegroundColor Yellow
    } else {
        git push origin v2.0-archive 2>$null
        Write-Host "  Created and pushed v2.0-archive branch" -ForegroundColor Green
    }
    git checkout main
} finally {
    Pop-Location
}

# Step 2: Remove old Python files
Write-Host "[2/5] Removing old Python v2.0 files..." -ForegroundColor Green
Push-Location $RepoPath
try {
    $foldersToRemove = @("src", "docs", "screenshots", "assets")
    $filesToRemove = @("build.ps1", "requirements.txt", "ROADMAP.md")

    foreach ($folder in $foldersToRemove) {
        if (Test-Path $folder) {
            git rm -rf $folder 2>$null
            Write-Host "  Removed: $folder/" -ForegroundColor Gray
        }
    }

    foreach ($file in $filesToRemove) {
        if (Test-Path $file) {
            git rm $file 2>$null
            Write-Host "  Removed: $file" -ForegroundColor Gray
        }
    }
} finally {
    Pop-Location
}

# Step 3: Copy new v3.0 files
Write-Host "[3/5] Copying new v3.0 files..." -ForegroundColor Green

# Files and folders to copy (excluding bin, obj, and other build artifacts)
$itemsToCopy = @(
    "App.xaml",
    "App.xaml.cs",
    "MainPage.xaml",
    "MainPage.xaml.cs",
    "GlobalUsings.cs",
    "FolderFreshLite.csproj",
    "README.md",
    ".gitignore",
    "Components",
    "Models",
    "Services",
    "Helpers",
    "Assets",
    "Platforms"
)

foreach ($item in $itemsToCopy) {
    $sourcePath = Join-Path $SourcePath $item
    $destPath = Join-Path $RepoPath $item

    if (Test-Path $sourcePath) {
        if (Test-Path $sourcePath -PathType Container) {
            # It's a directory
            if (Test-Path $destPath) {
                Remove-Item $destPath -Recurse -Force
            }
            Copy-Item $sourcePath $destPath -Recurse
            Write-Host "  Copied: $item/" -ForegroundColor Gray
        } else {
            # It's a file
            Copy-Item $sourcePath $destPath -Force
            Write-Host "  Copied: $item" -ForegroundColor Gray
        }
    }
}

# Step 4: Keep existing files that should be preserved
Write-Host "[4/5] Preserving existing files..." -ForegroundColor Green
$preserveFiles = @("LICENSE", "FUNDING.yml")
foreach ($file in $preserveFiles) {
    if (Test-Path (Join-Path $RepoPath $file)) {
        Write-Host "  Preserved: $file" -ForegroundColor Gray
    }
}

# Step 5: Stage changes
Write-Host "[5/5] Staging changes..." -ForegroundColor Green
Push-Location $RepoPath
try {
    git add -A
    Write-Host "  All changes staged" -ForegroundColor Gray
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Migration prepared successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. cd $RepoPath" -ForegroundColor White
Write-Host "  2. Review changes: git status" -ForegroundColor White
Write-Host "  3. Review diff: git diff --cached" -ForegroundColor White
Write-Host "  4. Commit: git commit -m 'v3.0.0 Beta - Complete rewrite in C#/.NET 9 with WinUI 3'" -ForegroundColor White
Write-Host "  5. Push: git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "Optional: Create a release tag" -ForegroundColor Cyan
Write-Host "  git tag -a v3.0.0-beta -m 'v3.0.0 Beta Release'" -ForegroundColor White
Write-Host "  git push origin v3.0.0-beta" -ForegroundColor White
