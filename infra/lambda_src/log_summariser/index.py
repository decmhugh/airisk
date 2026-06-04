"""
Scheduled Lambda – runs every hour.

Normal run:
  1. Always recompute today (day still in progress).
  2. Check yesterday – if already in DynamoDB, skip; otherwise summarise it.

Force run (invoke with {"force": true}):
  Scan ALL available dates in the S3 bucket and summarise every day found.
"""
import copy
import gzip
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

LOG_BUCKET = os.environ.get("LOG_BUCKET", "dmh-kb-docs")
LOG_PREFIX = os.environ.get("LOG_PREFIX", "airisk/AWSLogs/586794455900/BedrockModelInvocationLogs/eu-west-1")
DAILY_SUMMARY_TABLE = os.environ["DAILY_SUMMARY_TABLE"]

_s3      = boto3.client("s3")
_bedrock = boto3.client("bedrock")
_ddb     = boto3.resource("dynamodb")
_table   = _ddb.Table(DAILY_SUMMARY_TABLE)

# ── Model name resolution ─────────────────────────────────────────────────────

_MODEL_NAME_MAP: dict[str, str] = {
    # Anthropic Claude
    "anthropic.claude-3-5-sonnet-20241022-v2:0": "Claude 3.5 Sonnet v2",
    "anthropic.claude-3-5-sonnet-20240620-v1:0": "Claude 3.5 Sonnet",
    "anthropic.claude-3-5-haiku-20241022-v1:0":  "Claude 3.5 Haiku",
    "anthropic.claude-3-sonnet-20240229-v1:0":   "Claude 3 Sonnet",
    "anthropic.claude-3-haiku-20240307-v1:0":    "Claude 3 Haiku",
    "anthropic.claude-3-opus-20240229-v1:0":     "Claude 3 Opus",
    "anthropic.claude-instant-v1":               "Claude Instant",
    "anthropic.claude-v2:1":                     "Claude 2.1",
    "anthropic.claude-v2":                       "Claude 2",
    # Amazon Titan / Nova
    "amazon.titan-text-express-v1":              "Titan Text Express",
    "amazon.titan-text-lite-v1":                 "Titan Text Lite",
    "amazon.titan-text-premier-v1:0":            "Titan Text Premier",
    "amazon.titan-embed-text-v1":                "Titan Embed Text v1",
    "amazon.titan-embed-text-v2:0":              "Titan Embed Text v2",
    "amazon.nova-micro-v1:0":                    "Nova Micro",
    "amazon.nova-lite-v1:0":                     "Nova Lite",
    "amazon.nova-pro-v1:0":                      "Nova Pro",
    # Meta Llama
    "meta.llama3-8b-instruct-v1:0":              "Llama 3 8B",
    "meta.llama3-70b-instruct-v1:0":             "Llama 3 70B",
    "meta.llama3-1-8b-instruct-v1:0":            "Llama 3.1 8B",
    "meta.llama3-1-70b-instruct-v1:0":           "Llama 3.1 70B",
    "meta.llama3-2-1b-instruct-v1:0":            "Llama 3.2 1B",
    "meta.llama3-2-3b-instruct-v1:0":            "Llama 3.2 3B",
    "meta.llama3-2-11b-instruct-v1:0":           "Llama 3.2 11B",
    "meta.llama3-2-90b-instruct-v1:0":           "Llama 3.2 90B",
    # Mistral
    "mistral.mistral-7b-instruct-v0:2":          "Mistral 7B",
    "mistral.mixtral-8x7b-instruct-v0:1":        "Mixtral 8x7B",
    "mistral.mistral-large-2402-v1:0":           "Mistral Large",
    "mistral.mistral-small-2402-v1:0":           "Mistral Small",
    # Cohere
    "cohere.command-r-v1:0":                     "Command R",
    "cohere.command-r-plus-v1:0":                "Command R+",
    "cohere.embed-english-v3":                   "Cohere Embed EN",
    "cohere.embed-multilingual-v3":              "Cohere Embed ML",
    # AI21
    "ai21.j2-ultra-v1":                          "Jurassic-2 Ultra",
    "ai21.j2-mid-v1":                            "Jurassic-2 Mid",
    "ai21.jamba-instruct-v1:0":                  "Jamba Instruct",
    # Named agents (provisioned / inference profile)
    "77x7m2nb6605":                              "Cafe Ole (Nova Lite)",
    "634379ydrl9w":                              "Cafe Vedran (Nova Lite)",
}

_name_cache: dict = {}


def _resolve_model_name(model_key: str) -> str:
    """Return a friendly display name for a model key/ID."""
    if model_key in _name_cache:
        return _name_cache[model_key]
    # Strip cross-region inference prefix (us., eu., ap.)
    clean = model_key
    for pfx in ("us.", "eu.", "ap."):
        if model_key.startswith(pfx):
            clean = model_key[len(pfx):]
            break
    name = _MODEL_NAME_MAP.get(clean) or _MODEL_NAME_MAP.get(model_key)
    if name:
        _name_cache[model_key] = name
        return name
    # Try Bedrock API: provisioned throughput
    try:
        resp = _bedrock.get_provisioned_model_throughput(provisionedModelId=model_key)
        base_id   = resp.get("modelArn", "").split("/")[-1]
        base_name = _MODEL_NAME_MAP.get(base_id, base_id)
        pt_name   = resp.get("provisionedModelName", "")
        name = f"{base_name} ({pt_name})" if pt_name else f"{base_name} [Provisioned]"
    except ClientError:
        # Try as application inference profile
        try:
            resp = _bedrock.get_inference_profile(inferenceProfileIdentifier=model_key)
            name = resp.get("inferenceProfileName") or model_key
        except ClientError:
            name = model_key
    _name_cache[model_key] = name
    return name


# ── S3 helpers ────────────────────────────────────────────────────────────────

def _list_prefixes(prefix: str) -> list[str]:
    """Return immediate child key-segments under prefix (one level, delimiter '/')."""
    results = []
    paginator = _s3.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=LOG_BUCKET, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                results.append(cp["Prefix"].rstrip("/").split("/")[-1])
    except ClientError:
        pass
    return sorted(results)


def _all_dates_in_s3() -> list[str]:
    """Walk year/month/day prefixes and return every YYYY-MM-DD that has log files."""
    dates = []
    for yr in _list_prefixes(f"{LOG_PREFIX}/"):
        for mo in _list_prefixes(f"{LOG_PREFIX}/{yr}/"):
            for dd in _list_prefixes(f"{LOG_PREFIX}/{yr}/{mo}/"):
                dates.append(f"{yr}-{mo}-{dd}")
    return sorted(dates)


def _read_day_logs(date_str: str) -> list:
    """Return all parsed log records for the given YYYY-MM-DD date."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    prefix = f"{LOG_PREFIX}/{d.year:04d}/{d.month:02d}/{d.day:02d}/"
    records = []
    paginator = _s3.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=LOG_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                try:
                    raw = _s3.get_object(Bucket=LOG_BUCKET, Key=obj["Key"])["Body"].read()
                    if raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)
                    for line in raw.decode("utf-8").splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                except ClientError:
                    pass
    except ClientError:
        pass
    return records


# ── Aggregation ───────────────────────────────────────────────────────────────

def _summarise(records: list, date_str: str) -> dict:
    total = len(records)
    errors = 0
    input_tokens = 0
    output_tokens = 0
    by_model: dict = defaultdict(lambda: {"invocations": 0, "errors": 0, "input_tokens": 0, "output_tokens": 0})
    by_operation: dict = defaultdict(lambda: {"invocations": 0, "errors": 0})

    for r in records:
        is_err = bool(r.get("errorCode"))
        if is_err:
            errors += 1

        in_tok = (r.get("input") or {}).get("inputTokenCount") or 0
        out_tok = (r.get("output") or {}).get("outputTokenCount") or 0
        input_tokens += in_tok
        output_tokens += out_tok

        raw_model = r.get("modelId", "unknown")
        model_key = raw_model.split("/")[-1] if "/" in raw_model else raw_model
        by_model[model_key]["invocations"] += 1
        by_model[model_key]["input_tokens"] += in_tok
        by_model[model_key]["output_tokens"] += out_tok
        if is_err:
            by_model[model_key]["errors"] += 1

        op = r.get("operation", "unknown")
        by_operation[op]["invocations"] += 1
        if is_err:
            by_operation[op]["errors"] += 1

    model_names = {k: _resolve_model_name(k) for k in by_model}
    return {
        "date": date_str,
        "total_invocations": total,
        "errors": errors,
        "success": total - errors,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "by_model": {k: dict(v) for k, v in by_model.items()},
        "model_names": model_names,
        "by_operation": {k: dict(v) for k, v in by_operation.items()},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── DynamoDB helpers ──────────────────────────────────────────────────────────

def _to_decimal(obj):
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, int):
        return Decimal(obj)
    return obj


def _day_exists(date_str: str) -> bool:
    try:
        return "Item" in _table.get_item(Key={"date": date_str})
    except ClientError:
        return False


def _write_summary(summary: dict) -> None:
    _table.put_item(Item=_to_decimal(copy.deepcopy(summary)))


# ── Handler ───────────────────────────────────────────────────────────────────

def lambda_handler(event, _context):
    print(json.dumps(event))
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    force = bool(event.get("force", False)) if isinstance(event, dict) else False
    results = []

    if force:
        # ── Force run: summarise every date found in S3 ──────────────────────
        s3_dates = _all_dates_in_s3()
        print(f"Force run – found {len(s3_dates)} date(s) in S3: {s3_dates}")
        for date_str in s3_dates:
            records = _read_day_logs(date_str)
            _write_summary(_summarise(records, date_str))
            results.append({"date": date_str, "records": len(records), "action": "written"})
            print(f"  Written {date_str}: {len(records)} records")

    else:
        # ── Normal run: today + yesterday check ──────────────────────────────
        # Always refresh today (day is still in progress)
        print(f"Summarising today: {today_str}")
        records = _read_day_logs(today_str)
        _write_summary(_summarise(records, today_str))
        results.append({"date": today_str, "records": len(records), "action": "written"})

        # Yesterday – only if not already stored
        if _day_exists(yesterday_str):
            print(f"Yesterday ({yesterday_str}) already summarised – skipping.")
            results.append({"date": yesterday_str, "action": "skipped_exists"})
        else:
            print(f"Summarising yesterday: {yesterday_str}")
            records = _read_day_logs(yesterday_str)
            if records:
                _write_summary(_summarise(records, yesterday_str))
                results.append({"date": yesterday_str, "records": len(records), "action": "written"})
            else:
                results.append({"date": yesterday_str, "records": 0, "action": "skipped_empty"})

    print(f"Result: {results}")
    return {"statusCode": 200, "body": json.dumps(results)}
