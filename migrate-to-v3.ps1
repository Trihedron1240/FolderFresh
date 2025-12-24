# FolderFresh v2.0 to v3.0 Migration Script
# This script helps transition your repo from Python/PySide6 to C#/.NET 9

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath  # Path to your FolderFresh git repository (clone of GitHub repo)
)

$ErrorActionPreference = "Stop"
$SourcePath = $PSScriptRoot  # This script should be in the FolderFresh-development folder

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

Write-Host "Repository: $RepoPath" -ForegroundColor Yellow
Write-Host "Source: $SourcePath" -ForegroundColor Yellow
Write-Host ""

# Step 1: Create archive branch
Write-Host "[1/5] Creating v2.0-archive branch..." -ForegroundColor Green
Push-Location $RepoPath
try {
    # Check if we're already on main
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne "main" -and $currentBranch -ne "master") {
        git checkout main 2>$null
        if ($LASTEXITCODE -ne 0) {
            git checkout master 2>$null
        }
    }

    # Create archive branch
    git branch v2.0-archive 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Created v2.0-archive branch" -ForegroundColor Gray
    } else {
        Write-Host "  Branch v2.0-archive already exists" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

# Step 2: Remove old Python files
Write-Host "[2/5] Removing old Python v2.0 files..." -ForegroundColor Green
Push-Location $RepoPath
try {
    $foldersToRemove = @("src", "docs", "screenshots", "assets", "installer")
    $filesToRemove = @("build.ps1", "requirements.txt", "ROADMAP.md", "README.md", ".gitignore")

    foreach ($folder in $foldersToRemove) {
        if (Test-Path $folder) {
            Remove-Item $folder -Recurse -Force
            Write-Host "  Removed: $folder/" -ForegroundColor Gray
        }
    }

    foreach ($file in $filesToRemove) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "  Removed: $file" -ForegroundColor Gray
        }
    }
} finally {
    Pop-Location
}

# Step 3: Copy new v3.0 files
Write-Host "[3/5] Copying new v3.0 files..." -ForegroundColor Green

# Root-level files to copy
$rootFiles = @(
    "Directory.Build.props",
    "Directory.Build.targets",
    "Directory.Packages.props",
    "FolderFreshLite.sln",
    "global.json",
    ".editorconfig",
    ".vsconfig"
)

# Copy root files
foreach ($file in $rootFiles) {
    $src = Join-Path $SourcePath $file
    $dest = Join-Path $RepoPath $file
    if (Test-Path $src) {
        Copy-Item $src $dest -Force
        Write-Host "  Copied: $file" -ForegroundColor Gray
    }
}

# Copy FolderFreshLite folder (main source)
$srcFolder = Join-Path $SourcePath "FolderFreshLite"
$destFolder = Join-Path $RepoPath "FolderFreshLite"

# Items to copy from FolderFreshLite (excluding bin/obj)
$folderItems = @(
    "App.xaml",
    "App.xaml.cs",
    "MainPage.xaml",
    "MainPage.xaml.cs",
    "GlobalUsings.cs",
    "FolderFreshLite.csproj",
    "Components",
    "Models",
    "Services",
    "Helpers",
    "Assets",
    "Platforms"
)

# Create FolderFreshLite folder
if (-not (Test-Path $destFolder)) {
    New-Item -ItemType Directory -Path $destFolder | Out-Null
}

foreach ($item in $folderItems) {
    $src = Join-Path $srcFolder $item
    $dest = Join-Path $destFolder $item

    if (Test-Path $src) {
        if (Test-Path $src -PathType Container) {
            if (Test-Path $dest) {
                Remove-Item $dest -Recurse -Force
            }
            Copy-Item $src $dest -Recurse
            Write-Host "  Copied: FolderFreshLite/$item/" -ForegroundColor Gray
        } else {
            Copy-Item $src $dest -Force
            Write-Host "  Copied: FolderFreshLite/$item" -ForegroundColor Gray
        }
    }
}

# Copy README.md and .gitignore to repo root
$readmeSrc = Join-Path $srcFolder "README.md"
$readmeDest = Join-Path $RepoPath "README.md"
if (Test-Path $readmeSrc) {
    Copy-Item $readmeSrc $readmeDest -Force
    Write-Host "  Copied: README.md (to root)" -ForegroundColor Gray
}

$gitignoreSrc = Join-Path $srcFolder ".gitignore"
$gitignoreDest = Join-Path $RepoPath ".gitignore"
if (Test-Path $gitignoreSrc) {
    Copy-Item $gitignoreSrc $gitignoreDest -Force
    Write-Host "  Copied: .gitignore (to root)" -ForegroundColor Gray
}

# Copy config folders
$configFolders = @(".vscode", ".run")
foreach ($folder in $configFolders) {
    $src = Join-Path $SourcePath $folder
    $dest = Join-Path $RepoPath $folder
    if (Test-Path $src) {
        if (Test-Path $dest) {
            Remove-Item $dest -Recurse -Force
        }
        Copy-Item $src $dest -Recurse
        Write-Host "  Copied: $folder/" -ForegroundColor Gray
    }
}

# Step 4: Preserve existing files
Write-Host "[4/5] Checking preserved files..." -ForegroundColor Green
$preserveFiles = @("LICENSE", "FUNDING.yml")
foreach ($file in $preserveFiles) {
    $path = Join-Path $RepoPath $file
    if (Test-Path $path) {
        Write-Host "  Preserved: $file" -ForegroundColor Gray
    } else {
        Write-Host "  Missing (OK to add later): $file" -ForegroundColor Yellow
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
Write-Host "========================================" -ForegroundColor Green
Write-Host "Migration prepared successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. cd $RepoPath" -ForegroundColor White
Write-Host "  2. Review changes: git status" -ForegroundColor White
Write-Host "  3. Commit:" -ForegroundColor White
Write-Host "     git commit -m 'v3.0.0 Beta - Complete rewrite in C#/.NET 9 with WinUI 3'" -ForegroundColor Yellow
Write-Host "  4. Push:" -ForegroundColor White
Write-Host "     git push origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "Optional - Push the archive branch:" -ForegroundColor Cyan
Write-Host "  git push origin v2.0-archive" -ForegroundColor Yellow
Write-Host ""
Write-Host "Optional - Create a release tag:" -ForegroundColor Cyan
Write-Host "  git tag -a v3.0.0-beta -m 'v3.0.0 Beta Release'" -ForegroundColor Yellow
Write-Host "  git push origin v3.0.0-beta" -ForegroundColor Yellow
