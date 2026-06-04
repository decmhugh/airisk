import time
import uuid
from decimal import Decimal

from common import INCIDENTS_TABLE, json_response, parse_body


def lambda_handler(event, _context):
    payload = parse_body(event)
    incident_id = payload.get("incident_id", str(uuid.uuid4()))
    event_ts = int(payload.get("event_ts", int(time.time())))

    item = {
        "incident_id": incident_id,
        "event_ts": event_ts,
        "system": payload.get("system", "unknown"),
        "type": payload.get("type", "unknown"),
        "severity": payload.get("severity", "medium"),
        "duration_minutes": int(payload.get("duration_minutes", 0)),
        "financial_impact_eur": Decimal(str(payload.get("financial_impact_eur", 0))),
        "trigger": bool(payload.get("trigger", False)),
        "created_at": int(time.time()),
    }
    INCIDENTS_TABLE.put_item(Item=item)

    return json_response(201, {"incident": item})
