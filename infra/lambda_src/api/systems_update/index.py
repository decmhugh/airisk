import time
from decimal import Decimal

from common import AI_SYSTEMS_TABLE, json_response, parse_body


def lambda_handler(event, _context):
    system_id = (event.get("pathParameters") or {}).get("system_id")
    if not system_id:
        return json_response(400, {"error": "Missing system_id"})

    payload = parse_body(event)

    AI_SYSTEMS_TABLE.update_item(
        Key={"system_id": system_id},
        UpdateExpression=(
            "SET #n = :name, owner = :owner, use_case = :use_case, criticality = :criticality, "
            "risk_score = :risk_score, #s = :status, updated_at = :updated_at"
        ),
        ExpressionAttributeNames={
            "#n": "name",
            "#s": "status",
        },
        ExpressionAttributeValues={
            ":name": payload.get("name", "Unnamed System"),
            ":owner": payload.get("owner", "unknown"),
            ":use_case": payload.get("use_case", ""),
            ":criticality": payload.get("criticality", "Medium"),
            ":risk_score": Decimal(str(payload.get("risk_score", 0))),
            ":status": payload.get("status", "Monitoring"),
            ":updated_at": int(time.time()),
        },
        ReturnValues="ALL_NEW",
    )

    result = AI_SYSTEMS_TABLE.get_item(Key={"system_id": system_id})
    return json_response(200, {"system": result.get("Item", {})})
