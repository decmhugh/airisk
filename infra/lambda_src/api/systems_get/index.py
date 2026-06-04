from common import AI_SYSTEMS_TABLE, json_response


def lambda_handler(event, _context):
    system_id = (event.get("pathParameters") or {}).get("system_id")
    if not system_id:
        return json_response(400, {"error": "Missing system_id"})

    result = AI_SYSTEMS_TABLE.get_item(Key={"system_id": system_id})
    item = result.get("Item")
    if not item:
        return json_response(404, {"error": "System not found"})

    return json_response(200, {"system": item})
