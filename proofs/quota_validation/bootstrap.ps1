param()

$ErrorActionPreference = 'Stop'
$runtimeDirectory = Join-Path $PSScriptRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null

# Official pinned artifacts. No system install, registry or PATH changes.
$jarUrl = 'https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar'
$jarSha1 = 'bee4a54f3ee3d4afc347c3240ec2d9e93b075104'
$javaUrl = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jre_x64_windows_hotspot_21.0.12.1_1.zip'
$javaSha256 = 'd35f31e712f0fcf6ac5a093edc90204fbff22f720ba3950bd09d331d5e621636'

function Get-CheckedArtifact {
    param([string]$Url, [string]$Destination, [string]$Algorithm, [string]$Expected)
    if (-not (Test-Path -LiteralPath $Destination)) {
        Write-Output "Downloading $(Split-Path -Leaf $Destination)"
        Invoke-WebRequest -Uri $Url -OutFile $Destination -Headers @{ 'User-Agent' = 'SAGA-quota-model-validation' }
    }
    $actual = (Get-FileHash -LiteralPath $Destination -Algorithm $Algorithm).Hash.ToLowerInvariant()
    if ($actual -ne $Expected) {
        throw "Checksum mismatch for $Destination; expected $Expected, got $actual."
    }
}

$jarPath = Join-Path $runtimeDirectory 'tla2tools-1.7.4.jar'
$javaArchive = Join-Path $runtimeDirectory 'temurin-jre-21.0.12.1-windows-x64.zip'
Get-CheckedArtifact -Url $jarUrl -Destination $jarPath -Algorithm SHA1 -Expected $jarSha1
Get-CheckedArtifact -Url $javaUrl -Destination $javaArchive -Algorithm SHA256 -Expected $javaSha256

$javaDirectory = Join-Path $runtimeDirectory 'temurin21'
if (-not (Test-Path -LiteralPath $javaDirectory)) {
    Expand-Archive -LiteralPath $javaArchive -DestinationPath $javaDirectory
}
$javaExecutables = @(Get-ChildItem -LiteralPath $javaDirectory -Filter java.exe -File -Recurse)
if ($javaExecutables.Count -ne 1) { throw 'Expected exactly one extracted java.exe.' }
$javaPath = $javaExecutables[0].FullName
$javaVersion = @(& $javaPath -version 2>&1 | ForEach-Object { "$_" })
if ($LASTEXITCODE -ne 0) { throw 'Portable Java failed its version check.' }

$toolchain = [ordered]@{
    created_utc = [DateTime]::UtcNow.ToString('o')
    java = $javaPath
    jar = $jarPath
    java_version = $javaVersion
    jar_url = $jarUrl
    jar_release = 'v1.7.4'
    jar_sha1 = $jarSha1
    jar_sha256 = (Get-FileHash -LiteralPath $jarPath -Algorithm SHA256).Hash.ToLowerInvariant()
    java_archive_url = $javaUrl
    java_archive_sha256 = $javaSha256
    artifact_sources = @(
        'https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4',
        'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jre&os=windows&vendor=eclipse'
    )
}
$manifestPath = Join-Path $runtimeDirectory 'toolchain.json'
$toolchain | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "Toolchain ready: $manifestPath"
$javaVersion
