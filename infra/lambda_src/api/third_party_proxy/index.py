import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from common import get_third_party_secret, json_response, parse_body


def lambda_handler(event, _context):
    payload = parse_body(event)

    config = get_third_party_secret()
    endpoint = payload.get("endpoint") or config.get("endpoint")
    api_key = config.get("api_key")

    if not endpoint:
        return json_response(400, {"error": "No endpoint configured"})

    request_payload = payload.get("payload", {})
    req = urllib_request.Request(
        endpoint,
        data=json.dumps(request_payload).encode("utf-8"),
        method="POST",
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}" if api_key else "",
        },
    )

    try:
        with urllib_request.urlopen(req, timeout=15) as resp:
            response_text = resp.read().decode("utf-8")
            return json_response(200, {"status": resp.status, "response": json.loads(response_text)})
    except HTTPError as err:
        return json_response(err.code, {"status": err.code, "error": err.reason})
    except URLError as err:
        return json_response(502, {"status": 502, "error": str(err)})
