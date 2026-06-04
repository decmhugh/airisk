import base64
import json
import os
from decimal import Decimal

import boto3

DYNAMODB = boto3.resource("dynamodb")
SECRETS_MANAGER = boto3.client("secretsmanager")
BEDROCK = boto3.client("bedrock-runtime")

AI_SYSTEMS_TABLE = DYNAMODB.Table(os.environ["AI_SYSTEMS_TABLE"])
INCIDENTS_TABLE = DYNAMODB.Table(os.environ["INCIDENTS_TABLE"])
TRIGGERS_TABLE = DYNAMODB.Table(os.environ["TRIGGERS_TABLE"])
AGENT_MONITORING_TABLE = DYNAMODB.Table(os.environ["AGENT_MONITORING_TABLE"])
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "")
THIRD_PARTY_SECRET = os.environ.get("THIRD_PARTY_SECRET", "")


def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Type {type(value)} is not JSON serializable")


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, default=decimal_to_float),
    }


def parse_body(event):
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        decoded = base64.b64decode(raw).decode("utf-8")
        return json.loads(decoded)
    return json.loads(raw)


def get_third_party_secret():
    if not THIRD_PARTY_SECRET:
        return {}
    secret_value = SECRETS_MANAGER.get_secret_value(SecretId=THIRD_PARTY_SECRET)
    if "SecretString" in secret_value:
        return json.loads(secret_value["SecretString"])
    return {}
