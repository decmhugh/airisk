param(
    [string]$BackendBucket = "dmh-kb-docs",
    [string]$Environment = "dev",
    [string]$Region = "eu-west-1",
    [string]$StateKey = "airisk/dev/terraform.tfstate",
    [string]$CloudtrailBucket = "ai-risk-platform-prod-cloudtrail-586794455900",
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"

$infraDeployScript = Join-Path $PSScriptRoot "infra\deploy.ps1"
if (-not (Test-Path $infraDeployScript)) {
    throw "Expected script not found: $infraDeployScript"
}

& $infraDeployScript `
    -BackendBucket $BackendBucket `
    -Environment $Environment `
    -Region $Region `
    -StateKey $StateKey `
    -CloudtrailBucket $CloudtrailBucket `
    -AutoApprove:$AutoApprove
