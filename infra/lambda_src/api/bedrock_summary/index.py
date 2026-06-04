import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

DAILY_SUMMARY_TABLE = os.environ["DAILY_SUMMARY_TABLE"]


def _dec_to_native(obj):
    if isinstance(obj, Decimal):
        n = int(obj)
        return n if Decimal(n) == obj else float(obj)
    if isinstance(obj, dict):
        return {k: _dec_to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dec_to_native(v) for v in obj]
    return obj


def lambda_handler(event, _context):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DAILY_SUMMARY_TABLE)

    items = []
    try:
        resp = table.scan()
        items.extend(resp.get("Items", []))
        while "LastEvaluatedKey" in resp:
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))
        items = sorted(_dec_to_native(items), key=lambda x: x.get("date", ""), reverse=True)
    except ClientError as exc:
        items = [{"_error": str(exc)}]

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as fh:
        html = fh.read()

    payload = {
        "summaries": items,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    json_str = json.dumps(payload).replace("</", "<\\/")
    html = html.replace("__SUMMARY_DATA__", json_str)

    return {
        "statusCode": 200,
        "headers": {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"},
        "body": html,
    }
