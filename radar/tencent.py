import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from .bencher import NoRedirect
from .public_sources import plain


class LoginRequired(Exception):
    pass


def request_page(page, cookie):
    body = json.dumps({"page_id": page, "page_size": 12, "scope": "all",
                       "order_by": "published_desc"}).encode()
    request = urllib.request.Request(
        "https://tlabel.tencent.com/api/v1/expert_hall/packages", data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "Cookie": cookie, "Origin": "https://tlabel.tencent.com",
                 "Referer": "https://tlabel.tencent.com/expert/recruit",
                 "X-Requested-With": "XMLHttpRequest"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code in {301, 302, 303, 307, 308, 401, 403}:
            raise LoginRequired() from None
        raise RuntimeError("Tencent HTTP request failed") from None
    if payload.get("code") == 13:
        raise LoginRequired()
    if payload.get("code") != 0:
        raise ValueError("Tencent request rejected")
    return payload["data"]


def normalize(row):
    if row.get("status", "open") not in {"open", "nearly_full", "closing_soon"}:
        return None
    deadline = row.get("signup_deadline")
    if deadline:
        end = datetime.fromisoformat(deadline)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone(timedelta(hours=8)))
        if end <= datetime.now(timezone.utc):
            return None
    identifier = row["package_id"]
    title = row["package_name"]
    if not identifier or not isinstance(title, str) or not title.strip():
        raise ValueError("Invalid Tencent job identity")
    if row.get("price_visible") is False:
        salary = "审核通过后告知"
    else:
        amount = (f'{row.get("price_min", "?")}–{row.get("price_max", "?")}'
                  if row.get("price_mode") == "range" else str(row.get("unit_price", "?")))
        currency = "积分" if row.get("price_currency") == "point" or row.get("channel") == "internal" else "元"
        salary = amount + currency + "/" + (row.get("unit") or "计费单位见详情")
    tags = " ".join(row.get("tags") or [])
    return {"source_id": f'tencent:{row.get("source", "gdpval")}:{identifier}',
            "title": title, "description": plain(row.get("summary")) + " " + tags,
            "url": "https://tlabel.tencent.com/expert/recruit?package_id=" + quote(str(identifier), safe=""),
            "salary": salary, "published_at": "发布时间未提供",
            "qualification": "资历要求及报名资格以平台审核为准", "deadline": deadline}


def collect_tencent(platform):
    cookie = os.environ.get("TLABEL_COOKIE", "").strip()
    if not cookie:
        raise LoginRequired()
    if "\r" in cookie or "\n" in cookie or cookie.lower().startswith("cookie:"):
        raise ValueError("Invalid TLABEL_COOKIE format")
    jobs = []
    seen = set()
    expected = None
    for page in range(1, 51):
        data = request_page(page, cookie)
        rows, total = data["list"], data["total"]
        if not isinstance(rows, list) or type(total) is not int or total < 0:
            raise ValueError("Invalid Tencent pagination")
        if expected is not None and total != expected:
            raise ValueError("Tencent listing changed during pagination")
        expected = total
        for row in rows:
            identifier = (row.get("source", "gdpval"), str(row["package_id"]))
            if identifier in seen:
                raise ValueError("Repeated Tencent page")
            seen.add(identifier)
            job = normalize(row)
            if job:
                jobs.append(job)
        if len(seen) == total:
            return jobs
        if not rows or len(seen) > total:
            raise ValueError("Incomplete Tencent pagination")
        time.sleep(0.4)
    raise ValueError("Tencent pagination limit reached")
