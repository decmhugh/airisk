from common import json_response


def lambda_handler(_event, _context):
    return json_response(200, {"status": "ok"})
