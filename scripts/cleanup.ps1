#!/usr/bin/env pwsh
# Project cleanup script - removes temporary files and build artifacts

Write-Host "🧹 Cleaning up Sobel project..." -ForegroundColor Cyan

# Root directory temporary files
Write-Host "`n📁 Cleaning root directory..." -ForegroundColor Yellow
$rootFiles = @(
    "random_log*.txt",
    "sim_random.log",
    "tmp_*.py",
    "tmp_*.txt"
)
foreach ($pattern in $rootFiles) {
    Get-ChildItem -Path "." -Filter $pattern -ErrorAction SilentlyContinue | 
        ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "  ✓ Removed: $($_.Name)" -ForegroundColor Green
        }
}

# Simulation artifacts
Write-Host "`n📁 Cleaning sim/ directory..." -ForegroundColor Yellow
$simFiles = @(
    "sim/*.vvp",
    "sim/*.vcd",
    "sim/*.log",
    "sim/tmp_*.py",
    "sim/a.out"
)
foreach ($pattern in $simFiles) {
    Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | 
        ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "  ✓ Removed: $($_.Name)" -ForegroundColor Green
        }
}

# Python cache
Write-Host "`n📁 Cleaning Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path "." -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
    ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        Write-Host "  ✓ Removed: $($_.FullName)" -ForegroundColor Green
    }

# LaTeX temporary files
Write-Host "`n📁 Cleaning LaTeX temporary files..." -ForegroundColor Yellow
$latexFiles = @(
    "docs/*.aux",
    "docs/*.log",
    "docs/*.out",
    "docs/*.toc",
    "docs/*.fdb_latexmk",
    "docs/*.fls",
    "docs/*.synctex.gz"
)
foreach ($pattern in $latexFiles) {
    Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | 
        ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "  ✓ Removed: $($_.Name)" -ForegroundColor Green
        }
}

Write-Host "`n✨ Cleanup complete!" -ForegroundColor Cyan
Write-Host "Note: Build artifacts (*.mem files) in sim/golden/ are preserved." -ForegroundColor Gray
