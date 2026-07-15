$ErrorActionPreference = "Stop"

$resultRoot = "results\mcts_v118_32gb\production_50k_seed_118003"
$reviewRoot = "mcts_v118_seed_118003_50k_review"
$reviewZip  = "mcts_v118_seed_118003_50k_review.zip"

if (-not (Test-Path $resultRoot)) {
    throw "결과 폴더를 찾을 수 없습니다: $resultRoot"
}

Remove-Item -Recurse -Force $reviewRoot -ErrorAction SilentlyContinue
Remove-Item -Force $reviewZip -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path "$reviewRoot\result" | Out-Null

$coreFiles = @(
    "execution_result.json",
    "final_summary.json",
    "leaderboard.json",
    "best_route.json",
    "completed_routes_compact.json",
    "search_state.json",
    "progression.json"
)

foreach ($file in $coreFiles) {
    $source = Join-Path $resultRoot $file
    if (Test-Path $source) {
        Copy-Item $source "$reviewRoot\result\$file"
    }
}

$smallDirs = @(
    "routes",
    "logs",
    "reports"
)

foreach ($dir in $smallDirs) {
    $source = Join-Path $resultRoot $dir
    if (Test-Path $source) {
        Copy-Item -Recurse $source "$reviewRoot\result\$dir"
    }
}

$checkpointRoot = Join-Path $resultRoot "checkpoint"

if (Test-Path $checkpointRoot) {
    $resolvedCheckpointRoot = (Resolve-Path $checkpointRoot).Path

    Get-ChildItem $checkpointRoot -Recurse -File -Filter "*.json" |
        ForEach-Object {
            $relativePath = $_.FullName.Substring(
                $resolvedCheckpointRoot.Length + 1
            )

            $destination = Join-Path `
                "$reviewRoot\result\checkpoint" `
                $relativePath

            New-Item `
                -ItemType Directory `
                -Force `
                -Path (Split-Path $destination) |
                Out-Null

            Copy-Item $_.FullName $destination
        }
}

$checkpointJsonNames = @(
    "latest_manifest.json",
    "previous_manifest.json",
    "progression.json"
)

foreach ($file in $checkpointJsonNames) {
    $source = Join-Path $resultRoot $file
    if (Test-Path $source) {
        Copy-Item $source "$reviewRoot\result\$file"
    }
}

Copy-Item "data\mcts_plan_v118_32gb_3x50k.json" $reviewRoot
Copy-Item "PROJECT_PROGRESS_STATE.json" $reviewRoot

$resolvedResultRoot = (Resolve-Path $resultRoot).Path

$files = Get-ChildItem $resultRoot -Recurse -File |
    Sort-Object FullName |
    ForEach-Object {
        [PSCustomObject]@{
            path = $_.FullName.Substring(
                $resolvedResultRoot.Length + 1
            ).Replace("\", "/")
            bytes = $_.Length
            sha256 = (
                Get-FileHash $_.FullName -Algorithm SHA256
            ).Hash.ToLower()
        }
    }

$inventory = [PSCustomObject]@{
    schema_version = "1.0.0"
    stage_id = "production_50k_seed_118003"
    result_root = "results/mcts_v118_32gb/production_50k_seed_118003"
    file_count = @($files).Count
    total_bytes = (
        $files |
        Measure-Object -Property bytes -Sum
    ).Sum
    files = @($files)
}

$inventory |
    ConvertTo-Json -Depth 8 |
    Set-Content `
        "$reviewRoot\FULL_RESULT_FILE_INVENTORY.json" `
        -Encoding UTF8

Compress-Archive `
    -Path "$reviewRoot\*" `
    -DestinationPath $reviewZip `
    -CompressionLevel Optimal

Write-Host ""
Write-Host "완료:"
Get-Item $reviewZip | Select-Object Name, Length
Get-FileHash $reviewZip -Algorithm SHA256
