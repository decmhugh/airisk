import gzip
import io
import json
import os
from datetime import datetime, timezone
from urllib.parse import parse_qs

import boto3
from botocore.exceptions import ClientError

LOG_BUCKET = os.environ.get("LOG_BUCKET", "dmh-kb-docs")
LOG_PREFIX = os.environ.get("LOG_PREFIX", "airisk/AWSLogs/586794455900/BedrockModelInvocationLogs/eu-west-1")
MAX_RECORDS = int(os.environ.get("LOG_MAX_RECORDS", "2000"))


def _s3():
    return boto3.client("s3")


def _parse_qs(event):
    raw = event.get("queryStringParameters") or {}
    return {k: (v[0] if isinstance(v, list) else v) for k, v in raw.items()}


def _list_prefixes(s3, bucket, prefix):
    """Return immediate child prefixes (one level) under prefix."""
    prefixes = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            prefixes.append(cp["Prefix"].rstrip("/").split("/")[-1])
    return sorted(prefixes)


def _read_logs(s3, bucket, prefix):
    """List all objects under prefix, read and parse JSONL, return list of records."""
    records = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if len(records) >= MAX_RECORDS:
                break
            try:
                raw = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
                # Bedrock invocation logs are gzip-compressed
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                body = raw.decode("utf-8")
                for line in body.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                        if len(records) >= MAX_RECORDS:
                            break
            except ClientError:
                pass
    return records


def lambda_handler(event, _context):
    params = _parse_qs(event)

    bucket = params.get("bucket", LOG_BUCKET).strip().strip("/")
    prefix_base = params.get("prefix", LOG_PREFIX).strip().strip("/")
    date_str = params.get("date", "")    # YYYY-MM-DD
    hour_str = params.get("hour", "")    # HH (two digits)

    s3 = _s3()

    # ── Resolve available dates when none supplied ───────────────────────────
    browse_data = {}
    records = []
    current_prefix = None

    if date_str and hour_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            yy, mm, dd = f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}"
            hh = f"{int(hour_str):02d}"
            current_prefix = f"{prefix_base}/{yy}/{mm}/{dd}/{hh}/"
            records = _read_logs(s3, bucket, current_prefix)
        except (ValueError, ClientError) as exc:
            records = [{"_error": str(exc)}]

    elif date_str:
        # List hours for the given date
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            yy, mm, dd = f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}"
            hours = _list_prefixes(s3, bucket, f"{prefix_base}/{yy}/{mm}/{dd}/")
            browse_data = {"level": "hours", "date": date_str, "hours": hours}
        except ClientError as exc:
            browse_data = {"level": "hours", "date": date_str, "hours": [], "error": str(exc)}

    else:
        # Build year → month → day tree
        try:
            years = _list_prefixes(s3, bucket, f"{prefix_base}/")
            tree = {}
            for yr in years:
                months = _list_prefixes(s3, bucket, f"{prefix_base}/{yr}/")
                tree[yr] = {}
                for mo in months:
                    days = _list_prefixes(s3, bucket, f"{prefix_base}/{yr}/{mo}/")
                    tree[yr][mo] = days
            browse_data = {"level": "calendar", "tree": tree}
        except ClientError as exc:
            browse_data = {"level": "calendar", "tree": {}, "error": str(exc)}

    # ── Summarise ────────────────────────────────────────────────────────────
    payload = {
        "bucket": bucket,
        "prefix_base": prefix_base,
        "date": date_str,
        "hour": hour_str,
        "current_prefix": current_prefix,
        "records": records,
        "browse": browse_data,
        "truncated": len(records) >= MAX_RECORDS,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as fh:
        html = fh.read()

    def _ser(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    html = html.replace("__LOG_DATA__", json.dumps(payload, default=_ser))

    return {
        "statusCode": 200,
        "headers": {
            "content-type": "text/html; charset=utf-8",
            "cache-control": "no-store",
        },
        "body": html,
    }
