# find-agent-logs.ps1
# Discover CloudWatch log groups for Bedrock Agent and query recent errors.
# Usage: .\find-agent-logs.ps1 [-AgentId fa21t-jIxtI35cuA] [-Hours 4] [-QueryMode errors|all]

param(
    [string]$AgentId   = "fa21t-jIxtI35cuA",
    [string]$Region    = "eu-west-1",
    [int]   $Hours     = 4,
    [ValidateSet("errors","all")] [string]$QueryMode = "errors"
)

$now     = [DateTimeOffset]::UtcNow
$startTs = $now.AddHours(-$Hours).ToUnixTimeSeconds()
$endTs   = $now.ToUnixTimeSeconds()

Write-Host "`n=== Bedrock Agent Log Discovery ===" -ForegroundColor Cyan
Write-Host "Agent : $AgentId  |  Region : $Region  |  Last $Hours hr(s)`n"

# ── 1. Find relevant log groups ───────────────────────────────────────────────
$prefixes = @("/aws/bedrock/agents", "/aws/bedrock/agentcore", "/aws/lambda")
$allGroups = @()

foreach ($pfx in $prefixes) {
    try {
        $r = aws logs describe-log-groups `
                --log-group-name-prefix $pfx `
                --region $Region --output json 2>$null | ConvertFrom-Json
        if ($r -and $r.logGroups) {
            $allGroups += $r.logGroups.logGroupName
        }
    } catch { }
}

$matched = $allGroups | Where-Object { $_ -match "bedrock|agentcore|$AgentId" }

if (-not $matched) {
    Write-Warning "No Bedrock log groups found. All discovered groups:"
    $allGroups | ForEach-Object { Write-Host "  $_" }

    # Last-resort: list ALL log groups and grep
    Write-Host "`nFalling back to full log group scan..." -ForegroundColor Yellow
    $all = aws logs describe-log-groups --region $Region --output json | ConvertFrom-Json
    $matched = $all.logGroups.logGroupName | Where-Object { $_ -match "bedrock|agentcore|$AgentId" }
    if (-not $matched) {
        Write-Warning "Still nothing. Check AWS credentials and region."
        exit 1
    }
}

Write-Host "Log groups matched:" -ForegroundColor Green
$matched | ForEach-Object { Write-Host "  $_" }

# ── 2. Log Insights query ─────────────────────────────────────────────────────
# build --log-group-names arg array (max 50 groups)
$lgArgs = ($matched | Select-Object -First 50 | ForEach-Object { "--log-group-names"; $_ })

$query = if ($QueryMode -eq "errors") {
    "fields @timestamp, @message, @logStream | filter @message like /(?i)(error|exception|500|fail|fault)/ | sort @timestamp desc | limit 50"
} else {
    "fields @timestamp, @message, @logStream | sort @timestamp desc | limit 100"
}

Write-Host "`nRunning Log Insights query (mode=$QueryMode)..." -ForegroundColor Cyan

$qid = (aws logs start-query @lgArgs `
    --start-time $startTs `
    --end-time   $endTs `
    --query-string $query `
    --region $Region `
    --output json | ConvertFrom-Json).queryId

if (-not $qid) { Write-Error "Failed to start query."; exit 1 }
Write-Host "Query ID: $qid"

do {
    Start-Sleep -Seconds 2
    $res    = aws logs get-query-results --query-id $qid --region $Region --output json | ConvertFrom-Json
    $status = $res.status
    Write-Host "  $status..." -ForegroundColor DarkGray
} while ($status -in @("Running","Scheduled"))

$rows = $res.results
if (-not $rows -or $rows.Count -eq 0) {
    Write-Host "`nNo results in the last $Hours hour(s) for mode '$QueryMode'." -ForegroundColor Yellow
} else {
    Write-Host "`n=== $($rows.Count) result(s) ===" -ForegroundColor Green
    foreach ($row in $rows) {
        $ts  = ($row | Where-Object { $_.field -eq "@timestamp" }).value
        $msg = ($row | Where-Object { $_.field -eq "@message"   }).value
        $ls  = ($row | Where-Object { $_.field -eq "@logStream" }).value
        Write-Host "[$ts]  $ls" -ForegroundColor DarkYellow
        Write-Host $msg
        Write-Host ("-" * 100) -ForegroundColor DarkGray
    }
}

# ── 3. Tail latest stream from the first matched group ────────────────────────
$firstGroup = $matched[0]
Write-Host "`n── Latest streams in: $firstGroup ──" -ForegroundColor Cyan

$streams = (aws logs describe-log-streams `
    --log-group-name $firstGroup `
    --order-by LastEventTime `
    --descending `
    --max-items 5 `
    --region $Region `
    --output json | ConvertFrom-Json).logStreams

if (-not $streams) {
    Write-Host "No streams found in $firstGroup" -ForegroundColor Yellow
    exit 0
}

$streams | ForEach-Object {
    $last = [DateTimeOffset]::FromUnixTimeMilliseconds($_.lastEventTimestamp).ToString("u")
    Write-Host "  $($_.logStreamName)  [last: $last]"
}

Write-Host "`nFetching last 30 events from: $($streams[0].logStreamName)`n" -ForegroundColor Cyan

$events = (aws logs get-log-events `
    --log-group-name  $firstGroup `
    --log-stream-name $streams[0].logStreamName `
    --start-from-head false `
    --limit 30 `
    --region $Region `
    --output json | ConvertFrom-Json).events

foreach ($e in $events) {
    $t = [DateTimeOffset]::FromUnixTimeMilliseconds($e.timestamp).ToString("HH:mm:ss")
    Write-Host "[$t] $($e.message)"
}
