from common import TRIGGERS_TABLE, json_response


def lambda_handler(_event, _context):
    return json_response(200, {"triggers": TRIGGERS_TABLE.scan().get("Items", [])})
