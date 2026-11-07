import hashlib
import re
from . import __version__
from .recommendations import recommendation, ai_workflow
from .details import pay_text, deadline_text
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def identity(job):
    if job.get("source_id"):
        return hashlib.sha256(job["source_id"].encode()).hexdigest()
    parts = urlsplit(job["url"])
    query = sorted((key, value) for key, value in parse_qsl(parts.query)
                   if not key.lower().startswith("utm_") and key.lower() not in {"ref", "source"})
    canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                           parts.path.rstrip("/"), urlencode(query), ""))
    return hashlib.sha256(canonical.encode()).hexdigest()


def score(job, rules):
    text = (job["title"] + " " + job["description"]).lower()
    reasons = []
    total = 0
    for rule in rules["categories"]:
        matches = [term for term in rule["terms"] if
                   (re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text)
                    if term.isascii() else term in text)]
        if matches:
            total += rule["weight"]
            reasons.append(rule["name"])
    return min(total, 100), reasons


def summarize(job):
    if job.get("analysis"):
        return job["analysis"]["summary"]
    text = re.sub(r"\s+", " ", job.get("description", "")).strip()
    sentences = [part.strip() for part in re.split(r"[。；\n]", text) if part.strip()]
    useful = next((part for part in sentences if any(word in part for word in
                   ("评审", "评测", "标注", "设计", "审核", "拍摄", "制作", "质检"))), "")
    return (useful[:90] + ("…" if len(useful) > 90 else "")) or "工作内容请查看岗位详情。"


def message(jobs, statuses, demo=False):
    lines = [f"AI 专家任务雷达 v{__version__} | AI Expert Job Radar" + ("【演示数据】" if demo else ""),
             f"新增匹配任务：{len(jobs)}"]
    current_platform = None
    for number, job in enumerate(jobs, 1):
        platform = job.get("platform_name", "岗位推荐")
        if platform != current_platform:
            lines.extend(["", "【" + platform + "】"])
            current_platform = platform
        salary = pay_text(job)
        lines.extend(["", f'{number}. {job["title"][:70]}', recommendation(job),
                      "做什么　" + summarize(job), "报酬　" + salary, "截止　" + deadline_text(job),
                      "AI参与　" + ai_workflow(job), job["url"]])
        if job.get("analysis"):
            analysis = job["analysis"]
            lines.extend(["推荐理由　" + analysis["fit_reason"], "门槛　" + analysis["requirements"],
                          "交付物　" + analysis["deliverables"], "注意　" + analysis["risks"]])
        lines.append(job.get("analysis_status", "规则初筛"))
    if not jobs:
        lines.append("今天暂无新的匹配机会。")
    successful = sum(": 读取 " in status for status in statuses)
    failures = [status.split(":", 1)[0] for status in statuses if "采集失败" in status]
    lines.extend(["", f"已检查{successful}个平台｜其余未接入",
                  "综合方向40、资格25、报酬信息15、期限信息10、AI可用性10分。未知资历最高4星。报酬以详情为准。"])
    if failures:
        lines.append("检查失败：" + "、".join(failures))
    if any("TLABEL_COOKIE" in status for status in statuses):
        lines.append("腾讯登录失效或未配置，请登录后更新 GitHub Secret TLABEL_COOKIE。")
    if any("COREXPERT_COOKIE" in status for status in statuses):
        lines.append("CoreXpert会话失效或访问受限，请检查 GitHub Secret COREXPERT_COOKIE。")
    return {"msg_type": "text", "content": {"text": "\n".join(lines)}}

