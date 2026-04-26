param(
    [Parameter(Mandatory = $true)]
    [string] $ArtifactDirectory
)

$resolved = Resolve-Path -LiteralPath $ArtifactDirectory
$files = Get-ChildItem -LiteralPath $resolved -File | Where-Object {
    $_.Name -notmatch '\.sha256$'
}

foreach ($file in $files) {
    $hash = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
    $line = "$($hash.Hash.ToLowerInvariant())  $($file.Name)"
    $checksumPath = "$($file.FullName).sha256"
    Set-Content -LiteralPath $checksumPath -Value $line -Encoding ascii
    Write-Host "Wrote $checksumPath"
}
