import base64
import hashlib
import hmac
import json
import os
import time
import urllib.request
from urllib.parse import urlsplit


def send(payload):
    url = os.environ.get("FEISHU_WEBHOOK_URL", "")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "open.feishu.cn"
            or not parsed.path.startswith("/open-apis/bot/v2/hook/")
            or not parsed.path.rsplit("/", 1)[-1] or parsed.query):
        raise ValueError("Set a valid FEISHU_WEBHOOK_URL")
    body = dict(payload)
    secret = os.environ.get("FEISHU_SIGNING_SECRET")
    if secret:
        timestamp = str(int(time.time()))
        key = f"{timestamp}\n{secret}".encode()
        body.update(timestamp=timestamp, sign=base64.b64encode(
            hmac.new(key, b"", hashlib.sha256).digest()).decode())
    data = json.dumps(body, ensure_ascii=False).encode()
    if len(data) > 19000:
        raise ValueError("Message too large; reduce batch_size")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
        result = json.load(response)
    if result.get("code", result.get("StatusCode", -1)) != 0:
        raise RuntimeError("Feishu rejected message")

