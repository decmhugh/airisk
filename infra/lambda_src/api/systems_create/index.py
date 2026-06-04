import time
import uuid
from decimal import Decimal

from common import AI_SYSTEMS_TABLE, json_response, parse_body


def lambda_handler(event, _context):
    payload = parse_body(event)

    system_id = payload.get("system_id") or str(uuid.uuid4())
    item = {
        "system_id": system_id,
        "name": payload.get("name", "Unnamed System"),
        "owner": payload.get("owner", "unknown"),
        "use_case": payload.get("use_case", ""),
        "criticality": payload.get("criticality", "Medium"),
        "risk_score": Decimal(str(payload.get("risk_score", 0))),
        "status": payload.get("status", "Monitoring"),
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }

    AI_SYSTEMS_TABLE.put_item(Item=item)
    return json_response(201, {"system": item})
