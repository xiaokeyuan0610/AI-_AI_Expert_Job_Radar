import json
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def collect_bencher(platform):
    url = "https://bencherai.com/api/tasks?page=1&pageSize=500&sort=published_desc"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "AIExpertJobRadar/0.1"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
        payload = json.load(response)
    return parse_jobs(payload)


def parse_jobs(payload):
    if payload.get("code") != 200:
        raise ValueError("Bencher API rejected request")
    data = payload["data"]
    rows = data["list"]
    if not isinstance(rows, list) or data["total"] != len(rows):
        raise ValueError("Incomplete job list; pagination needs review")
    jobs = []
    seen = set()
    for row in rows:
        identifier = row["id"]
        if type(identifier) is not int or identifier <= 0 or identifier in seen:
            raise ValueError("Invalid or duplicated job ID")
        seen.add(identifier)
        if not isinstance(row.get("title"), str) or not row["title"].strip():
            raise ValueError("Missing title")
        summary = row.get("summary") or ""
        if not isinstance(summary, str):
            raise ValueError("Invalid summary")
        jobs.append({"title": row["title"], "description": summary,
                     "url": f"https://bencherai.com/jobs?job={identifier}",
                     "salary": row.get("salary") or "未注明",
                     "published_at": row.get("publishedAt") or "未注明",
                     "source": "BencherAI 公共职位列表",
                     "qualification": "专业经历与硬性资格待核实"})
    return jobs
