param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$OutputName
)

$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Error $Message
    exit 1
}

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not ($OutputName.EndsWith(".skill.zip", [System.StringComparison]::OrdinalIgnoreCase))) {
    Fail "Output name must end with .skill.zip, for example: build\daee-epistemics-v0.4.0.0.skill.zip. GitHub Release assets should be the checked payload renamed to .skill; do not publish both .skill.zip and .skill, and do not re-zip the repo root."
}

if ([System.IO.Path]::IsPathRooted($OutputName)) {
    $OutputPath = [System.IO.Path]::GetFullPath($OutputName)
} else {
    $OutputPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $OutputName))
}

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
$PythonArgs = @()
if (-not $PythonCommand) {
    $PythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $PythonArgs = @("-3")
}
if (-not $PythonCommand) {
    Fail "Python 3 is required but neither python nor py was found on PATH."
}

$PackageScript = Join-Path $RepoRoot "tools\package_skill.py"
& $PythonCommand.Source @PythonArgs $PackageScript $OutputPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$Item = Get-Item -LiteralPath $OutputPath
$Hash = Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256

Write-Host ""
Write-Host "Packaged skill archive:"
Write-Host "  Path:   $($Item.FullName)"
Write-Host "  Size:   $($Item.Length) bytes"
Write-Host "  SHA256: $($Hash.Hash)"
Write-Host ""
Write-Host "Archive root contains the canonical scriptless runtime: SKILL.md, README.md, references/, compiled-module-map.json, and build-manifest.json from generated skill/."
Write-Host "Dev-only harness roots such as data/, scripts/, and tests/ are intentionally excluded from the canonical user-facing package."
