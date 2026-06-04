from common import AI_SYSTEMS_TABLE, json_response


def lambda_handler(_event, _context):
    systems = AI_SYSTEMS_TABLE.scan().get("Items", [])
    return json_response(200, {"systems": systems})
