[CmdletBinding(DefaultParameterSetName = "Run")]
param(
    [Parameter(Mandatory = $true, ParameterSetName = "Run")]
    [Parameter(Mandatory = $true, ParameterSetName = "ProofSidecarSelfTest")]
    [string]$Root,

    [Parameter(Mandatory = $true, ParameterSetName = "Run")]
    [string]$CaseName,

    [Parameter(Mandatory = $true, ParameterSetName = "Run")]
    [string]$PromptPath,

    [Parameter(Mandatory = $true, ParameterSetName = "Run")]
    [string]$RunDir,

    [Parameter(ParameterSetName = "Run")]
    [string]$Model = "gpt-5.5",

    [Parameter(ParameterSetName = "Run")]
    [string]$OutputBaseName = "",

    [Parameter(ParameterSetName = "Run")]
    [switch]$BuildProofSidecars,

    [Parameter(ParameterSetName = "Run")]
    [string]$RawInputPath = "",

    [Parameter(ParameterSetName = "Run")]
    [string]$ProofSidecarDir = "",

    [Parameter(Mandatory = $true, ParameterSetName = "ProofSidecarSelfTest")]
    [switch]$ProofSidecarSelfTest
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

function Invoke-ProofSidecarBuild(
    [string]$RootPath,
    [string]$RawInputFullPath,
    [string]$OutputPath,
    [string]$ProofSidecarDirPath,
    [string]$OutputBaseName
) {
    if (-not (Test-Path -LiteralPath $ProofSidecarDirPath -PathType Container)) {
        New-Item -ItemType Directory -Path $ProofSidecarDirPath | Out-Null
    }
    $ProofSidecarDirPath = (Resolve-Path -LiteralPath $ProofSidecarDirPath).Path

    $builderArgs = @(
        (Join-Path $RootPath "tools\build_retained_proof_sidecars.py"),
        "--input", $RawInputFullPath,
        "--output", $OutputPath,
        "--out-dir", $ProofSidecarDirPath,
        "--prefix", $OutputBaseName,
        "--force"
    )
    $builderOutput = & python @builderArgs 2>&1
    $builderExit = $LASTEXITCODE
    $builderOutput | ForEach-Object { Write-Host "$_" }
    if ($builderExit -ne 0) {
        throw "Proof sidecar build failed."
    }

    $proofCertificatePath = Join-Path $ProofSidecarDirPath "$OutputBaseName.collapse-certificate.json"
    $proofGrapherPath = Join-Path $ProofSidecarDirPath "$OutputBaseName.grapher.html"
    $proofHashesPath = Join-Path $ProofSidecarDirPath "$OutputBaseName.hashes.json"
    foreach ($path in @($proofCertificatePath, $proofGrapherPath, $proofHashesPath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Proof sidecar builder did not produce expected artifact: $path"
        }
    }

    return [pscustomobject]@{
        raw_input = [pscustomobject]@{
            path = $RawInputFullPath
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $RawInputFullPath).Hash
        }
        out_dir = $ProofSidecarDirPath
        collapse_certificate = [pscustomobject]@{
            path = $proofCertificatePath
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $proofCertificatePath).Hash
        }
        grapher_html = [pscustomobject]@{
            path = $proofGrapherPath
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $proofGrapherPath).Hash
        }
        hashes = [pscustomobject]@{
            path = $proofHashesPath
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $proofHashesPath).Hash
        }
        command = "python $($builderArgs -join ' ')"
    }
}

function Test-ProofSidecarRecord([object]$Record) {
    foreach ($key in @("raw_input", "collapse_certificate", "grapher_html", "hashes")) {
        $property = $Record.PSObject.Properties[$key]
        if ($null -eq $property) {
            throw "Proof sidecar record missing key: $key"
        }
        $entry = $property.Value
        $path = $entry.PSObject.Properties["path"].Value
        $sha256 = $entry.PSObject.Properties["sha256"].Value
        if ([string]::IsNullOrWhiteSpace($path)) {
            throw "Proof sidecar record missing path for: $key"
        }
        if ([string]::IsNullOrWhiteSpace($sha256)) {
            throw "Proof sidecar record missing sha256 for: $key"
        }
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Proof sidecar record path does not exist for ${key}: $path"
        }
    }
}

function Write-JsonUtf8NoBom([string]$PathValue, [object]$Payload) {
    $json = $Payload | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($PathValue, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

$rootPath = Resolve-RequiredDirectory -PathValue $Root -Name "Root"
$currentPath = (Resolve-Path -LiteralPath (Get-Location)).Path
if ($currentPath -ne $rootPath) {
    throw "Wrong current directory. Current='$currentPath'; expected Root='$rootPath'. Re-run from the explicit Root so the smoke cannot accidentally bind another workspace."
}

$requiredFiles = @(
    (Join-Path $rootPath "skill\SKILL.md"),
    (Join-Path $rootPath "tools\build_compiled_runtime.py"),
    (Join-Path $rootPath "tools\build_retained_proof_sidecars.py"),
    (Join-Path $rootPath "docs\audits\v0.4.3.0-implementaudit-orchestrator.md")
)

foreach ($required in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required workspace file missing: $required"
    }
}

$skillPath = Join-Path $rootPath "skill\SKILL.md"
$skillHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $skillPath).Hash

if ($PSCmdlet.ParameterSetName -eq "ProofSidecarSelfTest") {
    $selfTestCase = Join-Path $rootPath "tests\retained-proof-corpus\v0.4.3.0-schema-light\valid\sidecar-backed\cases\a9-science-source"
    $selfTestInput = Join-Path $selfTestCase "input.txt"
    $selfTestOutput = Join-Path $selfTestCase "output.md"
    $selfTestRoot = Join-Path $rootPath ".daee\validation"
    if (-not (Test-Path -LiteralPath $selfTestRoot -PathType Container)) {
        New-Item -ItemType Directory -Path $selfTestRoot | Out-Null
    }
    $selfTestDir = Join-Path $selfTestRoot ("current-skill-proof-sidecar-" + [System.Guid]::NewGuid().ToString("N"))
    $proofSidecarRecord = Invoke-ProofSidecarBuild -RootPath $rootPath -RawInputFullPath $selfTestInput -OutputPath $selfTestOutput -ProofSidecarDirPath $selfTestDir -OutputBaseName "self-test"
    Test-ProofSidecarRecord -Record $proofSidecarRecord
    $selfTestHashPath = Join-Path $selfTestDir "self-test.smoke.hashes.json"
    $selfTestHashRecord = [ordered]@{
        case_name = "proof-sidecar-self-test"
        skill = [ordered]@{
            path = $skillPath
            sha256 = $skillHash
        }
        output = [ordered]@{
            path = $selfTestOutput
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $selfTestOutput).Hash
        }
        proof_sidecars = $proofSidecarRecord
    }
    $selfTestJson = $selfTestHashRecord | ConvertTo-Json -Depth 5
    if ($selfTestJson -notmatch '"proof_sidecars"') {
        throw "Proof sidecar self-test did not serialize proof_sidecars into the hash record."
    }
    Write-JsonUtf8NoBom -PathValue $selfTestHashPath -Payload $selfTestHashRecord

    $hashCheckerOutput = & python (Join-Path $rootPath "tools\check_smoke_artifacts.py") --samples-only --no-release-artifacts --require-proof-sidecars --hash-record $selfTestHashPath 2>&1
    $hashCheckerExit = $LASTEXITCODE
    $hashCheckerOutput | ForEach-Object { Write-Host "$_" }
    if ($hashCheckerExit -ne 0) {
        throw "Proof sidecar self-test hash-record validation failed."
    }

    $promotionArgs = @(
        (Join-Path $rootPath "tools\promote_retained_proof_case.py"),
        "--source-only",
        "--hash-record", $selfTestHashPath
    )
    $promotionOutput = & python @promotionArgs 2>&1
    $promotionExit = $LASTEXITCODE
    $promotionOutput | ForEach-Object { Write-Host "$_" }
    if ($promotionExit -ne 0) {
        throw "Proof sidecar self-test promotion-helper check failed."
    }

    Write-Host "current-skill smoke proof-sidecar self-test: PASS"
    Write-Host "proof-sidecar certificate: $($proofSidecarRecord.collapse_certificate.path)"
    Write-Host "proof-sidecar grapher: $($proofSidecarRecord.grapher_html.path)"
    Write-Host "proof-sidecar hashes: $($proofSidecarRecord.hashes.path)"
    Write-Host "proof-sidecar smoke hash record: $selfTestHashPath"
    return
}

$promptFullPath = Resolve-PathUnderRoot -RootPath $rootPath -PathValue $PromptPath
if (-not (Test-Path -LiteralPath $promptFullPath -PathType Leaf)) {
    throw "PromptPath does not exist: $promptFullPath"
}
$promptFullPath = (Resolve-Path -LiteralPath $promptFullPath).Path

$rawInputFullPath = $null
if ($BuildProofSidecars) {
    if ([string]::IsNullOrWhiteSpace($RawInputPath)) {
        throw "RawInputPath is required when BuildProofSidecars is set."
    }
    $rawInputFullPath = Resolve-PathUnderRoot -RootPath $rootPath -PathValue $RawInputPath
    if (-not (Test-Path -LiteralPath $rawInputFullPath -PathType Leaf)) {
        throw "RawInputPath does not exist: $rawInputFullPath"
    }
    $rawInputFullPath = (Resolve-Path -LiteralPath $rawInputFullPath).Path
}

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
    "--ignore-user-config",
    "--ephemeral",
    "-C", $rootPath,
    "-s", "read-only",
    "-m", $Model,
    "-c", 'approval_policy="never"',
    "-c", "shell_environment_policy.inherit=none",
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

$proofSidecarRecord = $null
if (($codexExit -eq 0) -and $BuildProofSidecars) {
    if ([string]::IsNullOrWhiteSpace($ProofSidecarDir)) {
        $proofSidecarDirPath = Join-Path $runDirPath "proof-sidecars"
    }
    else {
        $proofSidecarDirPath = Resolve-PathUnderRoot -RootPath $rootPath -PathValue $ProofSidecarDir
    }
    $proofSidecarRecord = Invoke-ProofSidecarBuild -RootPath $rootPath -RawInputFullPath $rawInputFullPath -OutputPath $outputPath -ProofSidecarDirPath $proofSidecarDirPath -OutputBaseName $OutputBaseName
    Test-ProofSidecarRecord -Record $proofSidecarRecord
}

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
if ($null -ne $proofSidecarRecord) {
    $hashRecord["proof_sidecars"] = $proofSidecarRecord
}

Write-JsonUtf8NoBom -PathValue $hashPath -Payload $hashRecord

if ($codexExit -ne 0) {
    throw "codex exec failed for CaseName='$CaseName' with exit code $codexExit. See $logPath"
}

Write-Host "current-skill smoke: PASS"
Write-Host "case: $CaseName"
Write-Host "output: $outputPath"
Write-Host "log: $logPath"
Write-Host "exit: $exitPath"
Write-Host "hashes: $hashPath"
if ($null -ne $proofSidecarRecord) {
    Write-Host "proof-sidecar certificate: $($proofSidecarRecord.collapse_certificate.path)"
    Write-Host "proof-sidecar grapher: $($proofSidecarRecord.grapher_html.path)"
    Write-Host "proof-sidecar hashes: $($proofSidecarRecord.hashes.path)"
}
