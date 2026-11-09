"""Independent cloud timer entry point. Dispatch acceptance is not delivery success."""
import json
import os
import re
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main_handler(event, context):
    if event.get("Type") != "Timer":
        raise ValueError("Only timer events are accepted")
    token = os.environ.get("GITHUB_DISPATCH_TOKEN", "").strip()
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Missing cloud dispatch configuration")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/actions/workflows/radar.yml/dispatches",
        method="POST", data=json.dumps({"ref": "main", "inputs": {"force_send": False}}).encode(),
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "JobRadarCloudTimer"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
            if response.status != 204:
                raise RuntimeError("GitHub did not accept dispatch")
    except Exception:
        # Never log credentials, request headers, or raw response bodies.
        raise RuntimeError("Cloud dispatch failed; inspect cloud networking or token permissions") from None
    print("GitHub dispatch accepted; report delivery has not yet been verified.")
    return {"status": "dispatch_accepted", "delivery_verified": False}
