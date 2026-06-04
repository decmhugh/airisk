variable "project_name" {
  description = "Base name for all resources"
  type        = string
  default     = "ai-risk-platform"
}

variable "environment" {
  description = "Environment name (dev, stage, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "bedrock_model_id" {
  description = "Default Bedrock model ID used by API Lambda"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "third_party_api_secret_arn" {
  description = "Secrets Manager ARN containing third-party API credentials"
  type        = string
  default     = ""
}

variable "automation_schedule_expression" {
  description = "EventBridge schedule for automation jobs"
  type        = string
  default     = "rate(6 hours)"
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "v1"
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "bedrock_agent_names" {
  description = "Bedrock agent names to monitor on each automation run"
  type        = list(string)
  default = [
    "dmh-serv-agent-v3",
    "agent_vedrancafe",
    "agent-tf-quick"
  ]
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for Bedrock control-plane event auditing"
  type        = bool
  default     = true
}

variable "cloudtrail_s3_bucket_name" {
  description = "Optional pre-existing S3 bucket for CloudTrail logs; leave empty to create one"
  type        = string
  default     = ""
}

variable "log_bucket" {
  description = "S3 bucket that holds Bedrock model invocation logs"
  type        = string
  default     = "dmh-kb-docs"
}

variable "log_prefix" {
  description = "S3 key prefix for Bedrock invocation logs (without trailing slash)"
  type        = string
  default     = "airisk/AWSLogs/586794455900/BedrockModelInvocationLogs/eu-west-1"
}

variable "agent_core_log_prefix" {
  description = "S3 key prefix for Bedrock AgentCore runtime application logs (without trailing slash)"
  type        = string
  default     = "AWSLogs/586794455900/bedrockagentcoreruntimeapplicationlogs"
}
