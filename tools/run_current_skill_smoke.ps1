param(
    [Parameter(Mandatory = $true)]
    [string]$Root,

    [Parameter(Mandatory = $true)]
    [string]$CaseName,

    [Parameter(Mandatory = $true)]
    [string]$PromptPath,

    [Parameter(Mandatory = $true)]
    [string]$RunDir,

    [string]$Model = "gpt-5.5",

    [string]$OutputBaseName = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-RequiredDirectory([string]$PathValue, [string]$Name) {
    if (-not (Test-Path -LiteralPath $PathValue -PathType Container)) {
        throw "$Name does not exist or is not a directory: $PathValue"
    }
    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Resolve-PathUnderRoot([string]$RootPath, [string]$PathValue) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }
    return (Join-Path -Path $RootPath -ChildPath $PathValue)
}

function ConvertTo-SafeName([string]$Value) {
    $safe = $Value.Trim().ToLowerInvariant() -replace "[^a-z0-9._-]+", "-"
    $safe = $safe.Trim("-._")
    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "CaseName did not produce a safe output basename."
    }
    return $safe
}

$rootPath = Resolve-RequiredDirectory -PathValue $Root -Name "Root"
$currentPath = (Resolve-Path -LiteralPath (Get-Location)).Path
if ($currentPath -ne $rootPath) {
    throw "Wrong current directory. Current='$currentPath'; expected Root='$rootPath'. Re-run from the explicit Root so the smoke cannot accidentally bind another workspace."
}

$requiredFiles = @(
    (Join-Path $rootPath "skill\SKILL.md"),
    (Join-Path $rootPath "tools\build_compiled_runtime.py"),
    (Join-Path $rootPath "docs\audits\v0.4.3.0-implementaudit-orchestrator.md")
)

foreach ($required in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required workspace file missing: $required"
    }
}

$promptFullPath = Resolve-PathUnderRoot -RootPath $rootPath -PathValue $PromptPath
if (-not (Test-Path -LiteralPath $promptFullPath -PathType Leaf)) {
    throw "PromptPath does not exist: $promptFullPath"
}
$promptFullPath = (Resolve-Path -LiteralPath $promptFullPath).Path

$runDirPath = Resolve-PathUnderRoot -RootPath $rootPath -PathValue $RunDir
if (-not (Test-Path -LiteralPath $runDirPath -PathType Container)) {
    New-Item -ItemType Directory -Path $runDirPath | Out-Null
}
$runDirPath = (Resolve-Path -LiteralPath $runDirPath).Path

if ([string]::IsNullOrWhiteSpace($OutputBaseName)) {
    $OutputBaseName = ConvertTo-SafeName -Value $CaseName
}
else {
    $OutputBaseName = ConvertTo-SafeName -Value $OutputBaseName
}

$skillPath = Join-Path $rootPath "skill\SKILL.md"
$skillHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $skillPath).Hash
$promptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $promptFullPath
if ($promptText -notmatch ("(?m)^Runtime SHA256:\s*" + [regex]::Escape($skillHash) + "\s*$")) {
    throw "Prompt does not record the current generated skill SHA256. Expected Runtime SHA256: $skillHash in $promptFullPath"
}

$promptCapturePath = Join-Path $runDirPath "$OutputBaseName.prompt.txt"
$outputPath = Join-Path $runDirPath "$OutputBaseName.md"
$logPath = Join-Path $runDirPath "$OutputBaseName.codex-log.txt"
$exitPath = Join-Path $runDirPath "$OutputBaseName.exit.txt"
$hashPath = Join-Path $runDirPath "$OutputBaseName.hashes.json"

if (([System.IO.Path]::GetFullPath($promptFullPath)) -ne ([System.IO.Path]::GetFullPath($promptCapturePath))) {
    Copy-Item -LiteralPath $promptFullPath -Destination $promptCapturePath -Force
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$codexArgs = @(
    "exec",
    "-C", $rootPath,
    "-s", "read-only",
    "-m", $Model,
    "-c", 'approval_policy="never"',
    "-c", 'shell_environment_policy.inherit="all"',
    "--output-last-message", $outputPath,
    "-"
)

$oldErrorActionPreference = $ErrorActionPreference
$oldNativePreference = $null
$hasNativePreference = Test-Path Variable:\PSNativeCommandUseErrorActionPreference
if ($hasNativePreference) {
    $oldNativePreference = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
}
try {
    $ErrorActionPreference = "Continue"
    $promptText | & codex @codexArgs 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $logPath
    $codexExit = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $oldErrorActionPreference
    if ($hasNativePreference) {
        $PSNativeCommandUseErrorActionPreference = $oldNativePreference
    }
}
Set-Content -LiteralPath $exitPath -Encoding ASCII -Value $codexExit

$hashRecord = [ordered]@{
    case_name = $CaseName
    root = $rootPath
    model = $Model
    codex_exit = $codexExit
    skill = @{
        path = $skillPath
        sha256 = $skillHash
    }
    prompt = @{
        source_path = $promptFullPath
        captured_path = $promptCapturePath
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $promptCapturePath).Hash
    }
    output = @{
        path = $outputPath
        sha256 = if (Test-Path -LiteralPath $outputPath -PathType Leaf) { (Get-FileHash -Algorithm SHA256 -LiteralPath $outputPath).Hash } else { $null }
    }
    log = @{
        path = $logPath
        sha256 = if (Test-Path -LiteralPath $logPath -PathType Leaf) { (Get-FileHash -Algorithm SHA256 -LiteralPath $logPath).Hash } else { $null }
    }
    exit = @{
        path = $exitPath
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $exitPath).Hash
    }
    command = "codex $($codexArgs -join ' ')"
}

$hashRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $hashPath -Encoding UTF8

if ($codexExit -ne 0) {
    throw "codex exec failed for CaseName='$CaseName' with exit code $codexExit. See $logPath"
}

Write-Host "current-skill smoke: PASS"
Write-Host "case: $CaseName"
Write-Host "output: $outputPath"
Write-Host "log: $logPath"
Write-Host "exit: $exitPath"
Write-Host "hashes: $hashPath"
