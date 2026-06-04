from common import AI_SYSTEMS_TABLE, json_response


def lambda_handler(event, _context):
    system_id = (event.get("pathParameters") or {}).get("system_id")
    if not system_id:
        return json_response(400, {"error": "Missing system_id"})

    AI_SYSTEMS_TABLE.delete_item(Key={"system_id": system_id})
    return json_response(200, {"deleted": True, "system_id": system_id})
