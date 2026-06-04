from common import AI_SYSTEMS_TABLE, INCIDENTS_TABLE, TRIGGERS_TABLE, json_response


def lambda_handler(_event, _context):
    systems = AI_SYSTEMS_TABLE.scan().get("Items", [])
    incidents = INCIDENTS_TABLE.scan().get("Items", [])
    triggers = TRIGGERS_TABLE.scan().get("Items", [])

    scores = [float(item.get("risk_score", 0)) for item in systems]
    high_risk = [score for score in scores if score > 65]

    return json_response(
        200,
        {
            "number_of_ai_systems": len(systems),
            "average_ai_risk_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "high_risk_systems": len(high_risk),
            "critical_incidents_90_days": len(incidents),
            "insurance_trigger_events": len(triggers),
            "estimated_financial_exposure_eur": sum(
                float(item.get("financial_impact_eur", 0)) for item in incidents
            ),
        },
    )
