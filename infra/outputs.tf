output "api_base_url" {
  description = "Base URL for the platform HTTP API"
  value       = aws_apigatewayv2_stage.platform_stage.invoke_url
}

output "api_endpoint_lambda_names" {
  description = "Lambda functions for API endpoint handlers"
  value       = { for key, fn in aws_lambda_function.api_endpoint : key => fn.function_name }
}

output "automation_lambda_name" {
  description = "Lambda function for scheduled automation"
  value       = aws_lambda_function.automation_worker.function_name
}

output "change_capture_lambda_name" {
  description = "Lambda function that captures CloudTrail Bedrock change events"
  value       = aws_lambda_function.change_capture.function_name
}

output "bedrock_change_event_rule_name" {
  description = "EventBridge rule capturing Bedrock agent/alias CloudTrail changes"
  value       = aws_cloudwatch_event_rule.bedrock_agent_change_events.name
}

output "bedrock_monitoring_dashboard_name" {
  description = "CloudWatch dashboard for Bedrock monitoring and automation health"
  value       = aws_cloudwatch_dashboard.bedrock_monitoring.dashboard_name
}

output "dynamodb_tables" {
  description = "Core tables backing risk, incidents and trigger events"
  value = {
    ai_systems         = aws_dynamodb_table.ai_systems.name
    incidents          = aws_dynamodb_table.incidents.name
    insurance_triggers = aws_dynamodb_table.insurance_triggers.name
    agent_monitoring   = aws_dynamodb_table.agent_monitoring.name
  }
}
