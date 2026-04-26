param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$OutputName
)

$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Error $Message
    exit 1
}

function ConvertTo-WslPath($WindowsPath) {
    $FullPath = [System.IO.Path]::GetFullPath($WindowsPath)
    if ($FullPath -notmatch '^[A-Za-z]:\\') {
        Fail "Only drive-letter Windows paths can be converted to WSL paths: $FullPath"
    }
    $Drive = $FullPath.Substring(0, 1).ToLowerInvariant()
    $Rest = $FullPath.Substring(2).Replace('\', '/')
    return "/mnt/$Drive$Rest"
}

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillRoot = Join-Path $RepoRoot "skill"

if (-not (Test-Path -LiteralPath (Join-Path $SkillRoot "SKILL.md"))) {
    Fail "Missing skill/SKILL.md. Run this script from the daee-epistemics repository."
}

if (-not (Test-Path -LiteralPath (Join-Path $SkillRoot "references"))) {
    Fail "Missing skill/references. Cannot build a valid skill archive."
}

if (-not ($OutputName.EndsWith(".skill.zip", [System.StringComparison]::OrdinalIgnoreCase))) {
    Fail "Output name must end with .skill.zip, for example: daee-epistemics-v0.2.3.0.skill.zip"
}

$Wsl = Get-Command wsl -ErrorAction SilentlyContinue
if (-not $Wsl) {
    Fail "WSL is required but was not found on PATH."
}

if ([System.IO.Path]::IsPathRooted($OutputName)) {
    $OutputPath = [System.IO.Path]::GetFullPath($OutputName)
} else {
    $OutputPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $OutputName))
}

$RepoWsl = ConvertTo-WslPath $RepoRoot
$OutputWsl = ConvertTo-WslPath $OutputPath

$PythonScript = @'
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import sys

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
skill = repo / "skill"

if not (skill / "SKILL.md").is_file():
    raise SystemExit("missing skill/SKILL.md")
if not (skill / "references").is_dir():
    raise SystemExit("missing skill/references")

out.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    out.unlink()

paths = [skill / "SKILL.md", *sorted((skill / "references").rglob("*"))]

with ZipFile(out, "w", ZIP_DEFLATED) as zf:
    for path in paths:
        if path.is_dir():
            continue
        rel = path.relative_to(skill).as_posix()
        info = ZipInfo(rel)
        info.compress_type = ZIP_DEFLATED
        info.external_attr = (0o644 & 0xFFFF) << 16
        zf.writestr(info, path.read_bytes())

with ZipFile(out) as zf:
    names = zf.namelist()

bad = [name for name in names if name.startswith("skill/") or name.startswith("./") or "\\" in name]
if "SKILL.md" not in names:
    raise SystemExit("archive missing SKILL.md at root")
if not any(name.startswith("references/") for name in names):
    raise SystemExit("archive missing references/ at root")
if bad:
    raise SystemExit("archive has invalid root or separators: " + ", ".join(bad[:10]))

print(f"Archive: {out}")
print(f"Entries: {len(names)}")
print("Root check: PASS")
print("Separator check: PASS")
'@

$PythonScript | & wsl python3 - $RepoWsl $OutputWsl
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
Write-Host "Archive root contains SKILL.md and references/."
