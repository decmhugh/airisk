from boto3.dynamodb.conditions import Key

from common import AGENT_MONITORING_TABLE, json_response


def _to_bool(value):
    return str(value).strip().lower() in ["1", "true", "yes", "y"]


def lambda_handler(event, _context):
    params = event.get("queryStringParameters") or {}
    agent = (params.get("agent") or "").strip().lower()
    category = (params.get("category") or "").strip().upper()
    changes_only = _to_bool(params.get("changes_only", "false"))

    try:
        limit = int(params.get("limit", 100))
    except ValueError:
        limit = 100

    limit = min(max(limit, 1), 500)

    if category:
        response = AGENT_MONITORING_TABLE.query(
            IndexName="change_category_monitored_at_idx",
            KeyConditionExpression=Key("change_category").eq(category),
            ScanIndexForward=False,
            Limit=limit,
        )
        records = response.get("Items", [])
        if agent:
            records = [item for item in records if item.get("agent_key", "") == agent]
    elif agent:
        response = AGENT_MONITORING_TABLE.query(
            IndexName="agent_key_monitored_at_idx",
            KeyConditionExpression=Key("agent_key").eq(agent),
            ScanIndexForward=False,
            Limit=limit,
        )
        records = response.get("Items", [])
    else:
        records = AGENT_MONITORING_TABLE.scan().get("Items", [])
        records.sort(key=lambda item: int(item.get("monitored_at", 0)), reverse=True)
        records = records[:limit]

    if changes_only:
        records = [item for item in records if item.get("change_detected", False)]

    return json_response(
        200,
        {
            "count": len(records),
            "filters": {
                "agent": agent,
                "category": category,
                "changes_only": changes_only,
                "limit": limit,
            },
            "records": records,
        },
    )
