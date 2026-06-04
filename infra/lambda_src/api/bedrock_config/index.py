import json
import os
from datetime import datetime

import boto3


def _serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


def _list_all(client, method, result_key, **kwargs):
    """Paginate through a boto3 list call and return all items."""
    items = []
    paginator_methods = {
        "list_foundation_models": False,  # no paginator
    }
    try:
        if method == "list_foundation_models":
            resp = getattr(client, method)(**kwargs)
            return resp.get(result_key, [])

        # Use paginator if available
        try:
            paginator = client.get_paginator(method)
            for page in paginator.paginate(**kwargs):
                items.extend(page.get(result_key, []))
        except Exception:
            resp = getattr(client, method)(**kwargs)
            items = resp.get(result_key, [])
    except Exception as exc:
        return {"error": str(exc)}
    return items


def lambda_handler(_event, _context):
    region = os.environ.get("AWS_REGION", "eu-west-1")
    bedrock = boto3.client("bedrock", region_name=region)
    bedrock_agent = boto3.client("bedrock-agent", region_name=region)

    data = {"region": region, "fetched_at": datetime.utcnow().isoformat() + "Z"}

    # ── Foundation Models ────────────────────────────────────────────────────
    data["foundation_models"] = _list_all(
        bedrock, "list_foundation_models", "modelSummaries"
    )

    # ── Custom Models ────────────────────────────────────────────────────────
    data["custom_models"] = _list_all(
        bedrock, "list_custom_models", "modelSummaries"
    )

    # ── Agents + Aliases ─────────────────────────────────────────────────────
    agents = _list_all(bedrock_agent, "list_agents", "agentSummaries")
    if isinstance(agents, list):
        for agent in agents:
            agent_id = agent.get("agentId")
            aliases = _list_all(
                bedrock_agent,
                "list_agent_aliases",
                "agentAliasSummaries",
                agentId=agent_id,
            )
            agent["aliases"] = aliases if isinstance(aliases, list) else []
    data["agents"] = agents

    # ── Knowledge Bases ──────────────────────────────────────────────────────
    kbs = _list_all(bedrock_agent, "list_knowledge_bases", "knowledgeBaseSummaries")
    if isinstance(kbs, list):
        for kb in kbs:
            kb_id = kb.get("knowledgeBaseId")
            kb["data_sources"] = _list_all(
                bedrock_agent,
                "list_data_sources",
                "dataSourceSummaries",
                knowledgeBaseId=kb_id,
            )
    data["knowledge_bases"] = kbs

    # ── Guardrails ───────────────────────────────────────────────────────────
    data["guardrails"] = _list_all(bedrock, "list_guardrails", "guardrails")

    # ── Flows ────────────────────────────────────────────────────────────────
    try:
        flows = _list_all(bedrock_agent, "list_flows", "flowSummaries")
        if isinstance(flows, list):
            for flow in flows:
                flow_id = flow.get("id")
                flow["aliases"] = _list_all(
                    bedrock_agent,
                    "list_flow_aliases",
                    "flowAliasSummaries",
                    flowIdentifier=flow_id,
                )
        data["flows"] = flows
    except Exception as exc:
        data["flows"] = {"error": str(exc)}

    # ── Prompts ──────────────────────────────────────────────────────────────
    data["prompts"] = _list_all(bedrock_agent, "list_prompts", "promptSummaries")

    # ── Provisioned Throughput ───────────────────────────────────────────────
    data["provisioned_throughputs"] = _list_all(
        bedrock, "list_provisioned_model_throughputs", "provisionedModelSummaries"
    )

    # ── Inference Profiles ───────────────────────────────────────────────────
    data["inference_profiles"] = _list_all(
        bedrock, "list_inference_profiles", "inferenceProfileSummaries"
    )

    # ── Invocation Logging Config ────────────────────────────────────────────
    try:
        resp = bedrock.get_model_invocation_logging_configuration()
        data["logging_config"] = resp.get("loggingConfig", {})
    except Exception as exc:
        data["logging_config"] = {"error": str(exc)}

    # ── Render HTML ──────────────────────────────────────────────────────────
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as fh:
        html = fh.read()

    html = html.replace("__BEDROCK_DATA__", json.dumps(data, default=_serialize))

    return {
        "statusCode": 200,
        "headers": {
            "content-type": "text/html; charset=utf-8",
            "cache-control": "no-store",
        },
        "body": html,
    }
