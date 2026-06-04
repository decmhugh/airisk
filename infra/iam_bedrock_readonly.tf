# ---------------------------------------------------------------------------
# IAM Role: Bedrock Read-Only
# Grants Get / List / Describe / ListTagsForResource across all Bedrock
# resources. Intended for auditing, dashboards, and observability workloads.
# ---------------------------------------------------------------------------

variable "bedrock_readonly_role_principals" {
  description = "List of IAM principal ARNs allowed to assume the Bedrock read-only role (e.g. Lambda ARNs, user ARNs, role ARNs). Defaults to the current AWS account root."
  type        = list(string)
  default     = []
}

locals {
  # If no explicit principals supplied, fall back to the account root so any
  # authorised entity in the same account can assume the role via sts:AssumeRole.
  bedrock_readonly_principals = length(var.bedrock_readonly_role_principals) > 0 ? var.bedrock_readonly_role_principals : ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
}

# ---------------------------------------------------------------------------
# Assume-role trust policy
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "bedrock_readonly_assume_role" {
  statement {
    sid     = "AllowAssumeRole"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = local.bedrock_readonly_principals
    }
  }
}

# ---------------------------------------------------------------------------
# IAM Role
# ---------------------------------------------------------------------------
resource "aws_iam_role" "bedrock_readonly" {
  name               = "${local.name_prefix}-bedrock-readonly"
  description        = "Read-only access to all Amazon Bedrock services for ${var.project_name} (${var.environment})"
  assume_role_policy = data.aws_iam_policy_document.bedrock_readonly_assume_role.json

  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-bedrock-readonly"
    Purpose = "bedrock-observability"
  })
}

# ---------------------------------------------------------------------------
# Permission policy: Read / List / Describe across all Bedrock namespaces
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "bedrock_readonly_policy_doc" {
  statement {
    sid    = "BedrockReadListDescribe"
    effect = "Allow"

    actions = [
      # ---- Foundation models ----
      "bedrock:GetFoundationModel",
      "bedrock:ListFoundationModels",
      "bedrock:GetFoundationModelAvailability",

      # ---- Custom / fine-tuned models ----
      "bedrock:GetCustomModel",
      "bedrock:ListCustomModels",
      "bedrock:GetModelCustomizationJob",
      "bedrock:ListModelCustomizationJobs",
      "bedrock:GetModelCopyJob",
      "bedrock:ListModelCopyJobs",
      "bedrock:GetModelImportJob",
      "bedrock:ListModelImportJobs",
      "bedrock:GetImportedModel",
      "bedrock:ListImportedModels",

      # ---- Agents ----
      "bedrock:GetAgent",
      "bedrock:ListAgents",
      "bedrock:GetAgentAlias",
      "bedrock:ListAgentAliases",
      "bedrock:GetAgentVersion",
      "bedrock:ListAgentVersions",
      "bedrock:GetAgentKnowledgeBase",
      "bedrock:ListAgentKnowledgeBases",
      "bedrock:GetAgentActionGroup",
      "bedrock:ListAgentActionGroups",
      "bedrock:GetAgentCollaborator",
      "bedrock:ListAgentCollaborators",
      "bedrock:GetAgentMemory",

      # ---- Knowledge Bases ----
      "bedrock:GetKnowledgeBase",
      "bedrock:ListKnowledgeBases",
      "bedrock:GetDataSource",
      "bedrock:ListDataSources",
      "bedrock:GetIngestionJob",
      "bedrock:ListIngestionJobs",
      "bedrock:RetrieveAndGenerate",
      "bedrock:Retrieve",

      # ---- Guardrails ----
      "bedrock:GetGuardrail",
      "bedrock:ListGuardrails",

      # ---- Evaluation & Batch ----
      "bedrock:GetEvaluationJob",
      "bedrock:ListEvaluationJobs",
      "bedrock:GetModelInvocationJob",
      "bedrock:ListModelInvocationJobs",

      # ---- Prompt management ----
      "bedrock:GetPrompt",
      "bedrock:ListPrompts",

      # ---- Flows ----
      "bedrock:GetFlow",
      "bedrock:ListFlows",
      "bedrock:GetFlowAlias",
      "bedrock:ListFlowAliases",
      "bedrock:GetFlowVersion",
      "bedrock:ListFlowVersions",

      # ---- Logging & Invocation configuration ----
      "bedrock:GetModelInvocationLoggingConfiguration",

      # ---- Marketplace / Provisioned throughput ----
      "bedrock:GetProvisionedModelThroughput",
      "bedrock:ListProvisionedModelThroughputs",
      "bedrock:GetMarketplaceModelEndpoint",
      "bedrock:ListMarketplaceModelEndpoints",

      # ---- Inference profiles ----
      "bedrock:GetInferenceProfile",
      "bedrock:ListInferenceProfiles",

      # ---- Tagging (read) ----
      "bedrock:ListTagsForResource",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "bedrock_readonly_policy" {
  name        = "${local.name_prefix}-bedrock-readonly-policy"
  description = "Grants Get/List/Describe/ListTagsForResource on all Bedrock resources"
  policy      = data.aws_iam_policy_document.bedrock_readonly_policy_doc.json

  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-bedrock-readonly-policy"
    Purpose = "bedrock-observability"
  })
}

resource "aws_iam_role_policy_attachment" "bedrock_readonly_attachment" {
  role       = aws_iam_role.bedrock_readonly.name
  policy_arn = aws_iam_policy.bedrock_readonly_policy.arn
}

# Allow the platform Lambda execution role to read Bedrock config (used by
# the /bedrock-config endpoint).
resource "aws_iam_role_policy_attachment" "lambda_bedrock_readonly" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.bedrock_readonly_policy.arn
}
