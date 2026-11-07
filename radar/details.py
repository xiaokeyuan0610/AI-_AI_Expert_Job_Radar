import re
from datetime import datetime, timedelta, timezone

CHINA = timezone(timedelta(hours=8))


def deadline_at(job):
    value = job.get("deadline")
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)) or re.fullmatch(r"\d+(\.\d+)?", str(value)):
            timestamp = float(value)
            if timestamp > 100000000000:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, CHINA)
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.replace(tzinfo=CHINA) if result.tzinfo is None else result.astimezone(CHINA)
    except (ValueError, OverflowError, OSError):
        return None


def deadline_text(job, now=None):
    end = deadline_at(job)
    if end is None:
        return "平台未注明"
    now = now or datetime.now(CHINA)
    seconds = (end - now).total_seconds()
    if seconds <= 0:
        status = "已截止"
    elif seconds <= 86400:
        status = "⏰ 24小时内截止"
    elif seconds <= 3 * 86400:
        status = "⏰ 3天内截止"
    else:
        status = f"剩余约{int(seconds / 86400)}天"
    return end.strftime("%m月%d日 %H:%M") + "（北京时间，" + status + "）"


def pay_text(job):
    text = str(job.get("salary") or "平台未注明")
    for source, target in {"BY_COUNT": "按量，具体单位待确认", "BY_TIME": "按时，具体单位待确认",
                           "hour": "小时", "month": "月", "project": "项目", "task": "题",
                           "CNY": "元"}.items():
        text = text.replace(source, target)
    return re.sub(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[–-]\s*\1(?![\d.])", r"\1", text)
