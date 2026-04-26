param(
    [Parameter(Mandatory = $true)]
    [string] $ArtifactDirectory,

    [string[]] $Include = @("*")
)

$resolved = Resolve-Path -LiteralPath $ArtifactDirectory
$files = foreach ($pattern in $Include) {
    Get-ChildItem -LiteralPath $resolved -File -Filter $pattern
}

$files = $files | Where-Object { $_.Name -notmatch '\.sha256$' } | Sort-Object FullName -Unique

foreach ($file in $files) {
    $hash = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
    $line = "$($hash.Hash.ToLowerInvariant())  $($file.Name)"
    $checksumPath = "$($file.FullName).sha256"
    Set-Content -LiteralPath $checksumPath -Value $line -Encoding ascii
    Write-Host "Wrote $checksumPath"
}
