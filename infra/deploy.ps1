param(
    [string]$BackendBucket = "dmh-kb-docs",
    [string]$Environment = "dev",
    [string]$Region = "eu-west-1",
    [string]$StateKey = "airisk/dev/terraform.tfstate",
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "Starting Terraform deployment..." -ForegroundColor Cyan
Write-Host "Bucket: $BackendBucket | Region: $Region | Env: $Environment | StateKey: $StateKey"

terraform fmt -recursive
if ($LASTEXITCODE -ne 0) { throw "terraform fmt failed with exit code $LASTEXITCODE" }

terraform init -reconfigure `
    "-backend-config=bucket=$BackendBucket" `
    "-backend-config=key=$StateKey" `
    "-backend-config=region=$Region" `
    "-backend-config=encrypt=true"
if ($LASTEXITCODE -ne 0) { throw "terraform init failed with exit code $LASTEXITCODE" }

$planFile = "tfplan"
terraform plan -var "environment=$Environment" -var "aws_region=$Region" -out $planFile
if ($LASTEXITCODE -ne 0) { throw "terraform plan failed with exit code $LASTEXITCODE" }

if ($AutoApprove) {
    terraform apply -auto-approve $planFile
}
else {
    terraform apply $planFile
}
if ($LASTEXITCODE -ne 0) { throw "terraform apply failed with exit code $LASTEXITCODE" }

Write-Host "Deployment complete." -ForegroundColor Green
