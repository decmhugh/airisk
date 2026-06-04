from collections import defaultdict
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from common import AGENT_MONITORING_TABLE, json_response


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ["1", "true", "yes", "y"]


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _record_day(record):
    monitored_at = _to_int(record.get("monitored_at", 0), 0)
    if monitored_at <= 0:
        return "unknown"
    return datetime.fromtimestamp(monitored_at, tz=timezone.utc).strftime("%Y-%m-%d")


def _record_change_types(record):
    change_types = record.get("change_types") or []
    if change_types:
        return [str(change_type) for change_type in change_types]

    if record.get("change_detected", False):
        return ["CHANGE_DETECTED"]

    return ["NO_CHANGE"]


def _load_records(agent, category, limit):
    if agent:
        response = AGENT_MONITORING_TABLE.query(
            IndexName="agent_key_monitored_at_idx",
            KeyConditionExpression=Key("agent_key").eq(agent),
            ScanIndexForward=False,
            Limit=limit,
        )
        records = response.get("Items", [])
    elif category:
        response = AGENT_MONITORING_TABLE.query(
            IndexName="change_category_monitored_at_idx",
            KeyConditionExpression=Key("change_category").eq(category),
            ScanIndexForward=False,
            Limit=limit,
        )
        records = response.get("Items", [])
    else:
        records = AGENT_MONITORING_TABLE.scan().get("Items", [])
        records.sort(key=lambda item: _to_int(item.get("monitored_at", 0), 0), reverse=True)
        records = records[:limit]

    if category and agent:
        records = [item for item in records if item.get("change_category", "") == category]

    return records


def lambda_handler(event, _context):
    params = event.get("queryStringParameters") or {}
    agent = (params.get("agent") or "").strip().lower()
    category = (params.get("category") or "").strip().upper()
    changes_only = _to_bool(params.get("changes_only"), default=True)
    limit = min(max(_to_int(params.get("limit"), 250), 1), 1000)

    records = _load_records(agent, category, limit)

    if changes_only:
        records = [item for item in records if item.get("change_detected", False)]

    daily_counts = defaultdict(lambda: defaultdict(int))
    daily_totals = defaultdict(int)
    change_types_seen = set()

    for record in records:
        day = _record_day(record)
        for change_type in _record_change_types(record):
            daily_counts[day][change_type] += 1
            daily_totals[day] += 1
            change_types_seen.add(change_type)

    days = []
    ordered_change_types = sorted(change_types_seen)
    for day in sorted(daily_counts.keys()):
        counts = {change_type: daily_counts[day].get(change_type, 0) for change_type in ordered_change_types}
        days.append(
            {
                "day": day,
                "total": daily_totals[day],
                "counts": counts,
            }
        )

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
            "change_types": ordered_change_types,
            "days": days,
        },
    )
