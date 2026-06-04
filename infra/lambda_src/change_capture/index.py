import os
import time
import uuid

import boto3
from botocore.exceptions import ClientError

DYNAMODB = boto3.resource("dynamodb")
AGENT_MONITORING_TABLE = DYNAMODB.Table(os.environ["AGENT_MONITORING_TABLE"])


def _safe_get(data, path, default=""):
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def _build_agent_key(agent_id, agent_name):
    if agent_id:
        return f"id:{str(agent_id).lower()}"
    if agent_name:
        return f"name:{str(agent_name).lower()}"
    return "unknown"


def lambda_handler(event, _context):
    detail = event.get("detail", {}) if isinstance(event, dict) else {}

    event_id = str(event.get("id", ""))
    event_name = str(detail.get("eventName", "UNKNOWN"))
    event_time = str(event.get("time", ""))
    monitored_at = int(time.time())

    request_params = detail.get("requestParameters", {})
    response_elements = detail.get("responseElements", {})

    agent_id = _safe_get(request_params, ["agentId"], "") or _safe_get(response_elements, ["agent", "agentId"], "")
    agent_name = _safe_get(request_params, ["agentName"], "") or _safe_get(response_elements, ["agent", "agentName"], "")
    alias_id = _safe_get(request_params, ["agentAliasId"], "")
    alias_name = _safe_get(request_params, ["agentAliasName"], "")

    agent_key = _build_agent_key(agent_id, agent_name)
    monitor_id = f"evt-{event_id}" if event_id else f"evt-{uuid.uuid4()}"

    item = {
        "monitor_id": monitor_id,
        "agent_key": agent_key,
        "monitored_at": monitored_at,
        "change_category": "EVENT",
        "change_detected": True,
        "change_types": ["CLOUDTRAIL_EVENT", event_name],
        "agent_name": agent_name,
        "resolved_agent_name": agent_name,
        "agent_id": agent_id,
        "agent_status": "EVENT_CAPTURED",
        "alias_count": 1 if alias_id or alias_name else 0,
        "aliases": [
            {
                "agentAliasId": alias_id,
                "agentAliasName": alias_name,
                "agentAliasStatus": "EVENT_CAPTURED",
                "updatedAt": event_time,
            }
        ]
        if alias_id or alias_name
        else [],
        "event_id": event_id,
        "event_name": event_name,
        "event_time": event_time,
        "event_source": str(detail.get("eventSource", "")),
        "event_user_arn": _safe_get(detail, ["userIdentity", "arn"], ""),
        "event_request_parameters": request_params,
    }

    try:
        AGENT_MONITORING_TABLE.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(monitor_id)",
        )
        return {
            "captured": True,
            "deduplicated": False,
            "event_id": event_id,
            "event_name": event_name,
            "monitor_id": monitor_id,
        }
    except ClientError as err:
        if err.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return {
                "captured": False,
                "deduplicated": True,
                "event_id": event_id,
                "event_name": event_name,
                "monitor_id": monitor_id,
            }
        raise
