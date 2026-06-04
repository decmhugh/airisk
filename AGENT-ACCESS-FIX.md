# Fix: AccessDeniedException — Claude Haiku 4.5 on AgentCore

## Error Summary

```
AccessDeniedException: Model access is denied due to IAM user or service role is not
authorized to perform the required AWS Marketplace actions
(aws-marketplace:ViewSubscriptions, aws-marketplace:Subscribe)

Model: global.anthropic.claude-haiku-4-5-20251001-v1:0
Agent: hosted_agent_fa21t-jIxtI35cuA  (eu-west-1)
```

## Root Causes

1. **Claude Haiku 4.5 is an AWS Marketplace model.** The Bedrock Model Access page has been retired — serverless models are now auto-enabled on first invocation. However, Marketplace-served models still require a user with `aws-marketplace:ViewSubscriptions` + `aws-marketplace:Subscribe` to invoke the model **once** to activate it account-wide.
2. **The AgentCore execution role** may not have `bedrock:InvokeModel` / `bedrock:Converse*` permission for this specific model ARN.

---

## Step 1 — Activate the Model (One-Time, Needs Marketplace Permissions)

The model access page is retired. For AWS Marketplace models, a user (or role) that has `aws-marketplace:ViewSubscriptions` and `aws-marketplace:Subscribe` must invoke the model once to enable it account-wide.

Run this as an admin user / role that has Marketplace permissions:

```powershell
aws bedrock invoke-model `
  --region eu-west-1 `
  --model-id "anthropic.claude-haiku-4-5-20251001-v1:0" `
  --body ([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(
      '{"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
  ))) `
  --content-type "application/json" `
  --accept "application/json" `
  outfile.json ; Remove-Item outfile.json -ErrorAction SilentlyContinue
```

If this succeeds, the model is now activated for all users in the account.  
If it fails with the same Marketplace error, the invoking role still lacks Marketplace permissions — attach the AWS managed policy **`AWSMarketplaceManageSubscriptions`** to it temporarily, re-run, then detach.

> **Note:** For first-time Anthropic model use you may be prompted to accept Anthropic's EULA via the AWS Console before the CLI invoke succeeds. Navigate to **Bedrock → Foundation models → Claude Haiku 4.5** and accept if prompted.

---

## Step 2 — Verify the AgentCore Execution Role Has Bedrock Permissions

Find the role the hosted agent runs as:

```powershell
aws bedrock-agentcore get-agent-runtime `
  --agent-runtime-id fa21t-jIxtI35cuA `
  --region eu-west-1 `
  --query "agentRuntime.roleArn"
```

Then check its attached policies allow `bedrock:ConverseStream` and `bedrock:InvokeModel`:

```powershell
$roleArn = aws bedrock-agentcore get-agent-runtime `
  --agent-runtime-id fa21t-jIxtI35cuA `
  --region eu-west-1 `
  --query "agentRuntime.roleArn" --output text

$roleName = $roleArn.Split("/")[-1]

aws iam simulate-principal-policy `
  --policy-source-arn $roleArn `
  --action-names bedrock:ConverseStream bedrock:InvokeModel `
  --resource-arns "arn:aws:bedrock:eu-west-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0" `
  --region eu-west-1
```

If the result is `implicitDeny` or `explicitDeny`, attach a policy:

```powershell
# Create the policy document
$policy = @{
  Version = "2012-10-17"
  Statement = @(@{
    Sid      = "AllowClaudeHaiku45"
    Effect   = "Allow"
    Action   = @(
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:Converse",
      "bedrock:ConverseStream"
    )
    Resource = @(
      "arn:aws:bedrock:eu-west-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
      "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
    )
  })
} | ConvertTo-Json -Depth 5

aws iam put-role-policy `
  --role-name $roleName `
  --policy-name AllowClaudeHaiku45 `
  --policy-document $policy `
  --region eu-west-1
```

---

## Step 3 — Handle `global.` Cross-Region Inference Prefix (Optional)

The model ID used is `global.anthropic.claude-haiku-4-5-20251001-v1:0`.  
The `global.` prefix routes through **cross-region inference** — ensure the role also has:

```json
"Resource": [
  "arn:aws:bedrock:eu-west-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
  "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
  "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
]
```

Or simply use `"arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"` (wildcard region).

---

## Step 4 — Retry

Invoke the agent again. If still failing after completing Steps 1–3, wait 2 minutes and retry — Bedrock caches subscription state briefly.

---

## Alternative: Switch to a Pre-Approved Model

If Haiku 4.5 approval is blocked, edit the agent's model config to use a model already enabled in the account:

| Model | ID |
|---|---|
| Claude 3 Haiku | `anthropic.claude-3-haiku-20240307-v1:0` |
| Claude 3.5 Sonnet | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| Nova Lite | `amazon.nova-lite-v1:0` |

Check which models are currently enabled:

```powershell
aws bedrock list-foundation-models `
  --by-provider Anthropic `
  --region eu-west-1 `
  --query "modelSummaries[?modelLifecycle.status=='ACTIVE'].modelId" `
  --output table
```
