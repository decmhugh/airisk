import os


def lambda_handler(_event, _context):
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as file_handle:
        body = file_handle.read()

    return {
        "statusCode": 200,
        "headers": {
            "content-type": "text/html; charset=utf-8",
            "cache-control": "no-store",
        },
        "body": body,
    }
