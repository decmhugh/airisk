import gzip
import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

LOG_BUCKET   = os.environ.get("LOG_BUCKET",            "dmh-kb-docs")
LOG_PREFIX   = os.environ.get("AGENT_CORE_LOG_PREFIX",
                               "AWSLogs/586794455900/bedrockagentcoreruntimeapplicationlogs")
MAX_RECORDS  = int(os.environ.get("LOG_MAX_RECORDS", "2000"))


def _s3():
    return boto3.client("s3")


def _parse_qs(event):
    raw = event.get("queryStringParameters") or {}
    return {k: (v[0] if isinstance(v, list) else v) for k, v in raw.items()}


def _list_prefixes(s3, bucket, prefix):
    prefixes = []
    paginator = s3.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                prefixes.append(cp["Prefix"].rstrip("/").split("/")[-1])
    except ClientError:
        pass
    return sorted(prefixes)


def _is_year(s):
    return s.isdigit() and 2000 <= int(s) <= 2040


def _browse_from(s3, bucket, root):
    """Return browse data from root, handling any number of stream-level dirs
    before the YYYY/MM/DD tree."""
    children = _list_prefixes(s3, bucket, root.rstrip("/") + "/")
    if not children:
        return {"level": "empty"}
    years = [c for c in children if _is_year(c)]
    if years:
        tree = {}
        for yr in years:
            months = _list_prefixes(s3, bucket, f"{root}/{yr}/")
            tree[yr] = {}
            for mo in months:
                days = _list_prefixes(s3, bucket, f"{root}/{yr}/{mo}/")
                tree[yr][mo] = days
        return {"level": "calendar", "tree": tree}
    else:
        return {"level": "streams", "streams": children}


def _read_logs(s3, bucket, prefix):
    records = []
    paginator = s3.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if len(records) >= MAX_RECORDS:
                    break
                try:
                    raw = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
                    if raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)
                    body = raw.decode("utf-8")
                    for line in body.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            # Non-JSON line — store as raw string
                            records.append({"_raw": line})
                        if len(records) >= MAX_RECORDS:
                            break
                except ClientError:
                    pass
    except ClientError:
        pass
    return records


def lambda_handler(event, _context):
    params = _parse_qs(event)

    bucket      = params.get("bucket", LOG_BUCKET).strip().strip("/")
    prefix_base = params.get("prefix", LOG_PREFIX).strip().strip("/")
    sub_prefix  = params.get("sub_prefix", "").strip().strip("/")
    date_str    = params.get("date", "")   # YYYY-MM-DD
    hour_str    = params.get("hour", "")   # HH

    # Effective root: prefix_base + optional intermediate sub-path (region/stream/…)
    root = f"{prefix_base}/{sub_prefix}" if sub_prefix else prefix_base

    s3 = _s3()
    browse_data    = {}
    records        = []
    current_prefix = None

    if date_str and hour_str:
        try:
            d  = datetime.strptime(date_str, "%Y-%m-%d")
            yy, mm, dd = f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}"
            hh = f"{int(hour_str):02d}"
            current_prefix = f"{root}/{yy}/{mm}/{dd}/{hh}/"
            records = _read_logs(s3, bucket, current_prefix)
        except (ValueError, ClientError) as exc:
            records = [{"_error": str(exc)}]

    elif date_str:
        try:
            d  = datetime.strptime(date_str, "%Y-%m-%d")
            yy, mm, dd = f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}"
            hours = _list_prefixes(s3, bucket, f"{root}/{yy}/{mm}/{dd}/")
            browse_data = {"level": "hours", "date": date_str, "hours": hours}
        except (ValueError, ClientError) as exc:
            browse_data = {"level": "hours", "date": date_str, "hours": [], "error": str(exc)}

    else:
        try:
            browse_data = _browse_from(s3, bucket, root)
        except ClientError as exc:
            browse_data = {"level": "calendar", "tree": {}, "error": str(exc)}

    payload = {
        "bucket":          bucket,
        "prefix_base":     prefix_base,
        "sub_prefix":      sub_prefix,
        "date":            date_str,
        "hour":            hour_str,
        "current_prefix":  current_prefix,
        "records":         records,
        "browse":          browse_data,
        "truncated":       len(records) >= MAX_RECORDS,
        "fetched_at":      datetime.now(timezone.utc).isoformat(),
    }

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as fh:
        html = fh.read()

    def _ser(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    json_str = json.dumps(payload, default=_ser).replace("</", "<\\/")
    html = html.replace("__LOG_DATA__", json_str)

    return {
        "statusCode": 200,
        "headers": {
            "content-type": "text/html; charset=utf-8",
            "cache-control": "no-store",
        },
        "body": html,
    }
