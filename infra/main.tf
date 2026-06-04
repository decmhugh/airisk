locals {
  name_prefix            = "${var.project_name}-${var.environment}"
  cloudtrail_bucket_name = var.cloudtrail_s3_bucket_name != "" ? var.cloudtrail_s3_bucket_name : "${local.name_prefix}-cloudtrail-${data.aws_caller_identity.current.account_id}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  api_endpoint_lambdas = {
    dashboard_home = {
      route_key = "GET /"
      handler   = "dashboard.index.lambda_handler"
    }
    health = {
      route_key = "GET /health"
      handler   = "health.index.lambda_handler"
    }
    systems_list = {
      route_key = "GET /systems"
      handler   = "systems_list.index.lambda_handler"
    }
    systems_get = {
      route_key = "GET /systems/{system_id}"
      handler   = "systems_get.index.lambda_handler"
    }
    systems_create = {
      route_key = "POST /systems"
      handler   = "systems_create.index.lambda_handler"
    }
    systems_update = {
      route_key = "PUT /systems/{system_id}"
      handler   = "systems_update.index.lambda_handler"
    }
    systems_delete = {
      route_key = "DELETE /systems/{system_id}"
      handler   = "systems_delete.index.lambda_handler"
    }
    agent_monitoring_list = {
      route_key = "GET /agent-monitoring"
      handler   = "agent_monitoring_list.index.lambda_handler"
    }
    agent_timeline = {
      route_key = "GET /agent-monitoring/timeline"
      handler   = "agent_timeline.index.lambda_handler"
    }
    risk_overview = {
      route_key = "GET /risk-overview"
      handler   = "risk_overview.index.lambda_handler"
    }
    risk_register = {
      route_key = "GET /risk-register"
      handler   = "risk_register.index.lambda_handler"
    }
    incidents_create = {
      route_key = "POST /incidents"
      handler   = "incidents_create.index.lambda_handler"
    }
    insurance_triggers = {
      route_key = "GET /insurance-triggers"
      handler   = "insurance_triggers.index.lambda_handler"
    }
    bedrock_invoke = {
      route_key = "POST /bedrock/invoke"
      handler   = "bedrock_invoke.index.lambda_handler"
    }
    third_party_proxy = {
      route_key = "POST /third-party/proxy"
      handler   = "third_party_proxy.index.lambda_handler"
    }
    bedrock_config = {
      route_key = "GET /bedrock-config"
      handler   = "bedrock_config.index.lambda_handler"
    }
    bedrock_logs = {
      route_key = "GET /bedrock-logs"
      handler   = "bedrock_logs.index.lambda_handler"
    }
  }
}

data "archive_file" "api_endpoints_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/api"
  output_path = "${path.module}/lambda_src/api_endpoints.zip"
}

data "archive_file" "automation_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/automation"
  output_path = "${path.module}/lambda_src/automation.zip"
}

data "archive_file" "change_capture_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/change_capture"
  output_path = "${path.module}/lambda_src/change_capture.zip"
}

data "aws_caller_identity" "current" {}

resource "aws_dynamodb_table" "ai_systems" {
  name         = "${local.name_prefix}-ai-systems"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "system_id"

  attribute {
    name = "system_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "incidents" {
  name         = "${local.name_prefix}-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"
  range_key    = "event_ts"

  attribute {
    name = "incident_id"
    type = "S"
  }

  attribute {
    name = "event_ts"
    type = "N"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "insurance_triggers" {
  name         = "${local.name_prefix}-insurance-triggers"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trigger_id"

  attribute {
    name = "trigger_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "agent_monitoring" {
  name         = "${local.name_prefix}-agent-monitoring"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "monitor_id"

  attribute {
    name = "monitor_id"
    type = "S"
  }

  attribute {
    name = "agent_key"
    type = "S"
  }

  attribute {
    name = "monitored_at"
    type = "N"
  }

  global_secondary_index {
    name            = "agent_key_monitored_at_idx"
    hash_key        = "agent_key"
    range_key       = "monitored_at"
    projection_type = "ALL"
  }

  attribute {
    name = "change_category"
    type = "S"
  }

  global_secondary_index {
    name            = "change_category_monitored_at_idx"
    hash_key        = "change_category"
    range_key       = "monitored_at"
    projection_type = "ALL"
  }

  tags = local.common_tags
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${local.name_prefix}-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "platform_policy_doc" {
  statement {
    sid = "DynamoAccess"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Scan",
      "dynamodb:Query"
    ]
    resources = [
      aws_dynamodb_table.ai_systems.arn,
      aws_dynamodb_table.incidents.arn,
      aws_dynamodb_table.insurance_triggers.arn,
      aws_dynamodb_table.agent_monitoring.arn,
      "${aws_dynamodb_table.agent_monitoring.arn}/index/*"
    ]
  }

  statement {
    sid = "BedrockInvoke"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:ListAgents",
      "bedrock:GetAgent",
      "bedrock:ListAgentAliases",
      "bedrock:GetAgentAlias"
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadThirdPartySecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = var.third_party_api_secret_arn == "" ? ["*"] : [var.third_party_api_secret_arn]
  }

  statement {
    sid = "S3LogsRead"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.log_bucket}",
      "arn:aws:s3:::${var.log_bucket}/*",
    ]
  }
}

resource "aws_iam_policy" "platform_policy" {
  name   = "${local.name_prefix}-platform-policy"
  policy = data.aws_iam_policy_document.platform_policy_doc.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "platform_policy_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.platform_policy.arn
}

resource "aws_lambda_function" "api_endpoint" {
  for_each         = local.api_endpoint_lambdas
  function_name    = "${local.name_prefix}-${each.key}"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = each.value.handler
  filename         = data.archive_file.api_endpoints_zip.output_path
  source_code_hash = data.archive_file.api_endpoints_zip.output_base64sha256
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      AI_SYSTEMS_TABLE       = aws_dynamodb_table.ai_systems.name
      INCIDENTS_TABLE        = aws_dynamodb_table.incidents.name
      TRIGGERS_TABLE         = aws_dynamodb_table.insurance_triggers.name
      AGENT_MONITORING_TABLE = aws_dynamodb_table.agent_monitoring.name
      BEDROCK_MODEL_ID       = var.bedrock_model_id
      THIRD_PARTY_SECRET     = var.third_party_api_secret_arn
      AWS_ACCOUNT_REGION     = var.aws_region
      LOG_BUCKET             = var.log_bucket
      LOG_PREFIX             = var.log_prefix
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "automation_worker" {
  function_name    = "${local.name_prefix}-automation-worker"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "index.lambda_handler"
  filename         = data.archive_file.automation_lambda_zip.output_path
  source_code_hash = data.archive_file.automation_lambda_zip.output_base64sha256
  timeout          = 60
  memory_size      = 512

  environment {
    variables = {
      AI_SYSTEMS_TABLE       = aws_dynamodb_table.ai_systems.name
      INCIDENTS_TABLE        = aws_dynamodb_table.incidents.name
      TRIGGERS_TABLE         = aws_dynamodb_table.insurance_triggers.name
      AGENT_MONITORING_TABLE = aws_dynamodb_table.agent_monitoring.name
      BEDROCK_AGENT_NAMES    = jsonencode(var.bedrock_agent_names)
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "change_capture" {
  function_name    = "${local.name_prefix}-change-capture"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "index.lambda_handler"
  filename         = data.archive_file.change_capture_lambda_zip.output_path
  source_code_hash = data.archive_file.change_capture_lambda_zip.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      AGENT_MONITORING_TABLE = aws_dynamodb_table.agent_monitoring.name
    }
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "platform_http_api" {
  name          = "${local.name_prefix}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.allowed_origins
    allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-request-id"]
    max_age       = 300
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "platform_lambda_integration" {
  for_each               = local.api_endpoint_lambdas
  api_id                 = aws_apigatewayv2_api.platform_http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api_endpoint[each.key].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "endpoint_route" {
  for_each  = local.api_endpoint_lambdas
  api_id    = aws_apigatewayv2_api.platform_http_api.id
  route_key = each.value.route_key
  target    = "integrations/${aws_apigatewayv2_integration.platform_lambda_integration[each.key].id}"
}

resource "aws_apigatewayv2_stage" "platform_stage" {
  api_id      = aws_apigatewayv2_api.platform_http_api.id
  name        = var.api_stage_name
  auto_deploy = true
  tags        = local.common_tags
}

resource "aws_lambda_permission" "allow_apigw_invoke" {
  for_each      = local.api_endpoint_lambdas
  statement_id  = "AllowInvokeFromApiGateway-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_endpoint[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform_http_api.execution_arn}/*/*"
}

resource "aws_cloudwatch_event_rule" "automation_schedule" {
  name                = "${local.name_prefix}-automation-schedule"
  description         = "Runs recurring risk automation jobs"
  schedule_expression = var.automation_schedule_expression
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_rule" "bedrock_agent_change_events" {
  name        = "${local.name_prefix}-bedrock-agent-changes"
  description = "Captures CloudTrail Bedrock agent and alias API changes"
  event_pattern = jsonencode(
    {
      "source" : ["aws.bedrock"],
      "detail-type" : ["AWS API Call via CloudTrail"],
      "detail" : {
        "eventSource" : ["bedrock-agent.amazonaws.com", "bedrock.amazonaws.com"],
        "eventName" : [
          "CreateAgent",
          "UpdateAgent",
          "DeleteAgent",
          "PrepareAgent",
          "CreateAgentAlias",
          "UpdateAgentAlias",
          "DeleteAgentAlias"
        ]
      }
    }
  )
  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "automation_lambda_target" {
  rule      = aws_cloudwatch_event_rule.automation_schedule.name
  target_id = "automation-worker"
  arn       = aws_lambda_function.automation_worker.arn
}

resource "aws_cloudwatch_event_target" "bedrock_change_capture_target" {
  rule      = aws_cloudwatch_event_rule.bedrock_agent_change_events.name
  target_id = "change-capture"
  arn       = aws_lambda_function.change_capture.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke" {
  statement_id  = "AllowInvokeFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.automation_worker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.automation_schedule.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke_change_capture" {
  statement_id  = "AllowInvokeFromEventBridgeBedrockChanges"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.change_capture.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.bedrock_agent_change_events.arn
}

resource "aws_s3_bucket" "cloudtrail_logs" {
  count         = var.enable_cloudtrail && var.cloudtrail_s3_bucket_name == "" ? 1 : 0
  bucket        = local.cloudtrail_bucket_name
  force_destroy = false
  tags          = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "cloudtrail_logs" {
  count                   = var.enable_cloudtrail && var.cloudtrail_s3_bucket_name == "" ? 1 : 0
  bucket                  = aws_s3_bucket.cloudtrail_logs[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "cloudtrail_s3_policy" {
  count = var.enable_cloudtrail ? 1 : 0

  statement {
    sid    = "AWSCloudTrailAclCheck"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:GetBucketAcl"]
    resources = ["arn:aws:s3:::${local.cloudtrail_bucket_name}"]
  }

  statement {
    sid    = "AWSCloudTrailWrite"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${local.cloudtrail_bucket_name}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }
}

resource "aws_s3_bucket_policy" "cloudtrail_logs" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = local.cloudtrail_bucket_name
  policy = data.aws_iam_policy_document.cloudtrail_s3_policy[0].json
}

resource "aws_cloudtrail" "bedrock_audit" {
  count                         = var.enable_cloudtrail ? 1 : 0
  name                          = "${local.name_prefix}-trail"
  s3_bucket_name                = local.cloudtrail_bucket_name
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true
  tags                          = local.common_tags

  depends_on = [aws_s3_bucket_policy.cloudtrail_logs]
}

resource "aws_cloudwatch_metric_alarm" "automation_errors" {
  alarm_name          = "${local.name_prefix}-automation-errors"
  alarm_description   = "Automation worker Lambda errors"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.automation_worker.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  tags                = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "change_capture_errors" {
  alarm_name          = "${local.name_prefix}-change-capture-errors"
  alarm_description   = "Bedrock change capture Lambda errors"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.change_capture.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  tags                = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "automation_rule_failed_invocations" {
  alarm_name          = "${local.name_prefix}-automation-rule-failed-invocations"
  alarm_description   = "EventBridge failed invocations for automation scheduler"
  namespace           = "AWS/Events"
  metric_name         = "FailedInvocations"
  dimensions          = { RuleName = aws_cloudwatch_event_rule.automation_schedule.name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  tags                = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "bedrock_change_rule_failed_invocations" {
  alarm_name          = "${local.name_prefix}-bedrock-change-rule-failed-invocations"
  alarm_description   = "EventBridge failed invocations for Bedrock change capture"
  namespace           = "AWS/Events"
  metric_name         = "FailedInvocations"
  dimensions          = { RuleName = aws_cloudwatch_event_rule.bedrock_agent_change_events.name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  tags                = local.common_tags
}

resource "aws_cloudwatch_dashboard" "bedrock_monitoring" {
  dashboard_name = "${local.name_prefix}-bedrock-monitoring"
  dashboard_body = jsonencode(
    {
      widgets = [
        {
          type   = "metric"
          x      = 0
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Errors"
            region = var.aws_region
            view   = "timeSeries"
            metrics = [
              ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.automation_worker.function_name],
              ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.change_capture.function_name]
            ]
          }
        },
        {
          type   = "metric"
          x      = 12
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "EventBridge Rule Activity"
            region = var.aws_region
            view   = "timeSeries"
            metrics = [
              ["AWS/Events", "Invocations", "RuleName", aws_cloudwatch_event_rule.automation_schedule.name],
              ["AWS/Events", "FailedInvocations", "RuleName", aws_cloudwatch_event_rule.automation_schedule.name],
              ["AWS/Events", "Invocations", "RuleName", aws_cloudwatch_event_rule.bedrock_agent_change_events.name],
              ["AWS/Events", "FailedInvocations", "RuleName", aws_cloudwatch_event_rule.bedrock_agent_change_events.name]
            ]
          }
        },
        {
          type   = "metric"
          x      = 0
          y      = 6
          width  = 24
          height = 6
          properties = {
            title  = "Lambda Invocations and Duration"
            region = var.aws_region
            view   = "timeSeries"
            metrics = [
              ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.automation_worker.function_name],
              ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.automation_worker.function_name],
              ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.change_capture.function_name],
              ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.change_capture.function_name]
            ]
          }
        }
      ]
    }
  )
}
