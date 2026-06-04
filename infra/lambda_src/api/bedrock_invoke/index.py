import json

from common import BEDROCK, BEDROCK_MODEL_ID, json_response, parse_body


def lambda_handler(event, _context):
    payload = parse_body(event)
    prompt = payload.get("prompt", "Summarize current AI risk posture")
    model_id = payload.get("model_id", BEDROCK_MODEL_ID)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = BEDROCK.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    payload_text = response["body"].read().decode("utf-8")
    return json_response(200, json.loads(payload_text))
