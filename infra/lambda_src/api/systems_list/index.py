from common import AI_SYSTEMS_TABLE, json_response


def lambda_handler(_event, _context):
    items = AI_SYSTEMS_TABLE.scan().get("Items", [])
    return json_response(200, {"systems": items})
