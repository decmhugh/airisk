import os
import json
import time
import uuid
import hashlib
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

DYNAMODB = boto3.resource("dynamodb")
BEDROCK_AGENT = boto3.client("bedrock-agent")

AI_SYSTEMS_TABLE = DYNAMODB.Table(os.environ["AI_SYSTEMS_TABLE"])
INCIDENTS_TABLE = DYNAMODB.Table(os.environ["INCIDENTS_TABLE"])
TRIGGERS_TABLE = DYNAMODB.Table(os.environ["TRIGGERS_TABLE"])
AGENT_MONITORING_TABLE = DYNAMODB.Table(os.environ["AGENT_MONITORING_TABLE"])
BEDROCK_AGENT_NAMES = json.loads(os.environ.get("BEDROCK_AGENT_NAMES", "[]"))


def _compute_score(system_item):
    incident_penalty = Decimal("10") if system_item.get("last_incident_high", False) else Decimal("0")
    drift_score = Decimal(str(system_item.get("drift_score", 0)))
    uptime_score = Decimal(str(system_item.get("uptime_score", 100)))

    base = Decimal("35") + drift_score * Decimal("0.4") + (Decimal("100") - uptime_score) * Decimal("0.3")
    score = max(Decimal("0"), min(Decimal("100"), base + incident_penalty))
    return round(score, 2)


def _grade(score):
    if score < 20:
        return "AAA"
    if score < 35:
        return "AA"
    if score < 50:
        return "A"
    if score < 65:
        return "BBB"
    if score < 80:
        return "BB"
    return "B"


def _evaluate_triggers(incident_item):
    duration_minutes = int(incident_item.get("duration_minutes", 0))
    trigger = incident_item.get("trigger", False)

    if trigger and duration_minutes >= 240:
        return "Outage > 4h", "Band 3"
    if trigger and duration_minutes >= 60:
        return "Outage > 1h", "Band 2"
    if incident_item.get("type") == "accuracy_drop":
        return "Accuracy drop > 10%", "Band 1"

    return None, None


def _upsert_system_scores():
    systems = AI_SYSTEMS_TABLE.scan().get("Items", [])
    updates = 0

    for system in systems:
        score = _compute_score(system)
        grade = _grade(score)
        AI_SYSTEMS_TABLE.update_item(
            Key={"system_id": system["system_id"]},
            UpdateExpression="SET risk_score = :score, risk_grade = :grade, last_review_ts = :review",
            ExpressionAttributeValues={
                ":score": Decimal(str(score)),
                ":grade": grade,
                ":review": int(time.time()),
            },
        )
        updates += 1

    return updates


def _generate_trigger_events():
    incidents = INCIDENTS_TABLE.scan().get("Items", [])
    created = 0

    for incident in incidents:
        trigger_name, payout_band = _evaluate_triggers(incident)
        if not trigger_name:
            continue

        trigger_id = f"trg-{incident['incident_id']}-{incident['event_ts']}"
        TRIGGERS_TABLE.put_item(
            Item={
                "trigger_id": trigger_id,
                "incident_id": incident["incident_id"],
                "system": incident.get("system", "unknown"),
                "trigger": trigger_name,
                "payout_band": payout_band,
                "status": "Eligible",
                "created_at": int(time.time()),
                "event_ref": str(uuid.uuid4()),
            }
        )
        created += 1

    return created


def _list_agents_by_name():
    next_token = None
    agent_lookup = {}

    while True:
        params = {}
        if next_token:
            params["nextToken"] = next_token

        response = BEDROCK_AGENT.list_agents(**params)
        for agent in response.get("agentSummaries", []):
            name = agent.get("agentName", "")
            if name:
                agent_lookup[name.lower()] = agent

        next_token = response.get("nextToken")
        if not next_token:
            break

    return agent_lookup


def _list_agent_aliases(agent_id):
    aliases = []
    next_token = None

    while True:
        params = {"agentId": agent_id}
        if next_token:
            params["nextToken"] = next_token

        response = BEDROCK_AGENT.list_agent_aliases(**params)
        for alias in response.get("agentAliasSummaries", []):
            aliases.append(
                {
                    "agentAliasId": alias.get("agentAliasId", ""),
                    "agentAliasName": alias.get("agentAliasName", ""),
                    "agentAliasStatus": alias.get("agentAliasStatus", "UNKNOWN"),
                    "updatedAt": str(alias.get("updatedAt", "")),
                }
            )

        next_token = response.get("nextToken")
        if not next_token:
            break

    aliases.sort(key=lambda item: (item.get("agentAliasName", ""), item.get("agentAliasId", "")))
    return aliases


def _aliases_signature(aliases):
    encoded = json.dumps(aliases, sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _latest_history(agent_key):
    response = AGENT_MONITORING_TABLE.query(
        IndexName="agent_key_monitored_at_idx",
        KeyConditionExpression=Key("agent_key").eq(agent_key),
        ScanIndexForward=False,
        Limit=1,
    )
    items = response.get("Items", [])
    if items:
        return items[0]
    return None


def _monitor_bedrock_agents():
    if not BEDROCK_AGENT_NAMES:
        return {"configured": 0, "monitored": 0, "not_found": 0}

    now = int(time.time())
    lookup = _list_agents_by_name()
    monitored = 0
    not_found = 0
    statuses = []

    for configured_name in BEDROCK_AGENT_NAMES:
        agent_key = configured_name.lower()
        summary = lookup.get(configured_name.lower())
        if not summary:
            status = "NOT_FOUND"
            agent_id = ""
            resolved_name = configured_name
            aliases = []
            not_found += 1
        else:
            status = summary.get("agentStatus", "UNKNOWN")
            agent_id = summary.get("agentId", "")
            resolved_name = summary.get("agentName", configured_name)
            aliases = _list_agent_aliases(agent_id)

        alias_signature = _aliases_signature(aliases)
        previous = _latest_history(agent_key)
        change_types = []

        if not previous:
            change_types.append("INITIAL_SNAPSHOT")
        else:
            if previous.get("agent_status") != status:
                change_types.append("AGENT_STATUS_CHANGED")

            if previous.get("alias_signature") != alias_signature:
                change_types.append("ALIASES_CHANGED")

        change_detected = len(change_types) > 0

        AGENT_MONITORING_TABLE.put_item(
            Item={
                "monitor_id": str(uuid.uuid4()),
                "agent_key": agent_key,
                "monitored_at": now,
                "change_category": "SNAPSHOT",
                "agent_name": configured_name,
                "resolved_agent_name": resolved_name,
                "agent_id": agent_id,
                "agent_status": status,
                "aliases": aliases,
                "alias_count": len(aliases),
                "alias_signature": alias_signature,
                "change_detected": change_detected,
                "change_types": change_types,
                "previous_agent_status": previous.get("agent_status", "") if previous else "",
                "previous_alias_signature": previous.get("alias_signature", "") if previous else "",
            }
        )
        monitored += 1
        statuses.append(
            {
                "agent_name": configured_name,
                "agent_id": agent_id,
                "agent_status": status,
                "alias_count": len(aliases),
                "change_detected": change_detected,
                "change_types": change_types,
                "source": "scheduled_snapshot",
            }
        )

    return {
        "configured": len(BEDROCK_AGENT_NAMES),
        "monitored": monitored,
        "not_found": not_found,
        "statuses": statuses,
    }


def lambda_handler(event, _context):
    source = event.get("source", "manual") if isinstance(event, dict) else "manual"

    score_updates = _upsert_system_scores()
    new_triggers = _generate_trigger_events()
    agent_monitoring = _monitor_bedrock_agents()

    return {
        "source": source,
        "score_updates": score_updates,
        "new_trigger_events": new_triggers,
        "agent_monitoring": agent_monitoring,
        "executed_at": int(time.time()),
    }
