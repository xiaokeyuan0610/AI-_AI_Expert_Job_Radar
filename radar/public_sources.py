import html
import json
import re
import time
import urllib.request
from .bencher import NoRedirect


def fetch(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers={
        "Accept": "application/json", "Content-Type": "application/json",
        "User-Agent": "AIExpertJobRadar/0.1"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
        return json.load(response)


def plain(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def normalize(kind, row):
    if kind == "appen_public":
        if row["recruitmentStatus"] != "RUNNING":
            return None
        identifier = row["recruitmentId"]
        title = row["recruitmentName"]
        url = "https://eliteai.appen.com.cn/guest/recruitment/square"
        salary = f'{row.get("paymentStandardMin", "?")}–{row.get("paymentStandardMax", "?")}（计费类型 {row.get("paymentType", "未注明")}）'
        published = "接口未提供"
    elif kind == "talents_public":
        if row["status"] != "启用":
            return None
        identifier = row["jobId"]
        title = row["jobName"]
        url = f"https://www.talents-ai.com/jobs/{identifier}"
        salary = f'{row.get("salaryStart", "?")}–{row.get("salaryEnd", "?")} {row.get("currency", "")} / {row.get("salaryType", "未注明")}'
        published = row.get("createTime") or "未注明（非保证发布时间）"
    else:
        if row["online_status"] != 10:
            return None
        identifier = row["id"]
        title = row["title"]
        url = f"https://fellow.meetchances.com/jobs/{identifier}"
        salary = f'{row.get("salary_min", "?")}–{row.get("salary_max", "?")} / {row.get("salary_type", "未注明")}（币种以详情为准）'
        published = row.get("created_at") or "未注明（非保证发布时间）"
    if not identifier or not isinstance(title, str) or not title.strip():
        raise ValueError("Invalid job identity")
    return {"source_id": f"{kind}:{identifier}", "title": title,
            "description": plain(row.get("description")), "url": url,
            "salary": salary, "published_at": published,
            "qualification": "专业资格待核实；时间为平台记录，首次发现不等于今日新增"}


def collect_public(platform):
    kind = platform["method"]
    jobs = []
    received = 0
    identifiers = set()
    expected = None
    for page in range(50):
        if kind == "appen_public":
            result = fetch("https://eliteai.appen.com.cn/api-gw/um/recruitment/worker/anon/demand-recruitment/page-search",
                           {"pageIndex": page, "pageSize": 12, "dataRange": "NEW_ONLY", "rowFlag": False})
            if result.get("status") != 200:
                raise ValueError("Appen request rejected")
            data = result["data"]
            rows, total = data["results"], data["totalElements"]
            key = "recruitmentId"
        elif kind == "talents_public":
            result = fetch(f"https://www.talents-ai.com/api/v1/expert/jobs?page={page + 1}&pageSize=20&sortBy=create_time&sortOrder=desc")
            if result.get("success") is not True:
                raise ValueError("Talents request rejected")
            data = result["data"]
            rows, total = data["items"], data["total"]
            key = "jobId"
        elif kind == "fellow_public":
            result = fetch(f"https://service.meetchances.com/api/v1/jobs/?skip={page * 21}&limit=21&sort_by=publish_time&sort_order=desc")
            if result.get("status_code") != 0:
                raise ValueError("Fellow request rejected")
            data = result["data"]
            rows, total = data["items"], data["count"]
            key = "id"
        else:
            raise ValueError("Unknown public source")
        if not isinstance(rows, list) or type(total) is not int or total < 0:
            raise ValueError("Invalid pagination schema")
        if expected is not None and expected != total:
            raise ValueError("Listing changed during pagination; retry next run")
        expected = total
        for row in rows:
            identifier = row[key]
            if identifier in identifiers:
                raise ValueError("Repeated page or duplicate job")
            identifiers.add(identifier)
            job = normalize(kind, row)
            if job:
                jobs.append(job)
        received += len(rows)
        if received == total:
            return jobs
        if not rows or received > total:
            raise ValueError("Incomplete pagination")
        time.sleep(0.4)
    raise ValueError("Pagination safety limit reached")
