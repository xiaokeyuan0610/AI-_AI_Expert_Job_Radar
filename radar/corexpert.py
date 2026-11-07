import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from .bencher import NoRedirect
from .public_sources import plain


class CoreSessionRequired(Exception):
    pass


def request_page(page, cookie):
    body = {"PageRequest": {"PageNo": page, "PageSize": 12},
            "SearchGroup": {"LogicalOperator": "and", "Conditions": []}, "TabType": 0}
    request = urllib.request.Request(
        "https://www.corexpertdata.com/external/specialist/recruit/talent/card_list",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json",
            "Accept": "application/json", "Agw-Js-Conv": "str", "Cookie": cookie,
            "Origin": "https://www.corexpertdata.com",
            "Referer": "https://www.corexpertdata.com/operation/s/recruitment-square"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code in {301, 302, 303, 307, 308, 401, 403}:
            raise CoreSessionRequired() from None
        raise RuntimeError("CoreXpert HTTP request failed") from None
    if result.get("BaseResp", {}).get("StatusCode") != 0:
        raise CoreSessionRequired()
    return result


def normalize(entry):
    card = entry["Card"]
    row = card["OutReach"]
    if row.get("Status") != 2:
        return None
    deadline = int(row.get("EndTime") or 0) / 1000
    if deadline and deadline <= time.time():
        return None
    identifier, title = card["CardID"], row["Name"]
    if not identifier or not isinstance(title, str) or not title.strip():
        raise ValueError("Invalid CoreXpert identity")
    description = plain(row.get("Description"))
    requirements = plain(row.get("RequiredInfo"))
    return {"source_id": "corexpert:" + str(identifier), "title": title,
            "description": description + " 要求：" + requirements,
            "url": "https://www.corexpertdata.com/operation/s/recruitment-square",
            "salary": f'{row.get("MinPrice", "?")}–{row.get("MaxPrice", "?")}元（计费单位以详情为准）',
            "published_at": "创建于 " + datetime.fromtimestamp(int(row["CreatedTime"]), timezone.utc).isoformat(),
            "qualification": requirements, "deadline": deadline}


def collect_corexpert(platform):
    cookie = os.environ.get("COREXPERT_COOKIE", "").strip()
    if not cookie:
        raise CoreSessionRequired()
    if "\r" in cookie or "\n" in cookie or cookie.lower().startswith("cookie:"):
        raise ValueError("Invalid COREXPERT_COOKIE format")
    jobs, identifiers = [], set()
    expected = None
    for page in range(50):
        result = request_page(page, cookie)
        rows, total = result["Cards"], result["Total"]
        if not isinstance(rows, list) or type(total) is not int or total < 0:
            raise ValueError("Invalid CoreXpert schema")
        if expected is not None and total != expected:
            raise ValueError("CoreXpert list changed during pagination")
        expected = total
        for row in rows:
            identifier = row["Card"]["CardID"]
            if identifier in identifiers:
                raise ValueError("Repeated CoreXpert page")
            identifiers.add(identifier)
            job = normalize(row)
            if job:
                jobs.append(job)
        if len(identifiers) == total:
            return jobs
        if not rows or len(identifiers) > total:
            raise ValueError("Incomplete CoreXpert pagination")
        time.sleep(0.4)
    raise ValueError("CoreXpert pagination limit reached")
