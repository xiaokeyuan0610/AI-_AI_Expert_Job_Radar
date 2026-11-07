"""Compact Feishu cards shared by daily reports and manual previews."""
import html
import re
from urllib.parse import urlsplit
from . import __version__
from .details import pay_text, deadline_text
from .recommendations import recommendation, ai_workflow
from .core import summarize


def brief(value, limit=85):
    value = re.sub(r"\s+", " ", str(value or "待确认")).strip()
    value = value[:limit].rstrip("，；、 ") + ("…" if len(value) > limit else "")
    value = html.escape(value)
    return re.sub(r"([\\`*\[\]_])", r"\\\1", value)


def card_message(jobs, statuses=(), *, test=False, checked=None, part=None):
    platform = jobs[0].get("platform_name", "岗位推荐") if jobs else "今日概览"
    heading = f"{platform} · {'样式测试' if test else '今日机会'}"
    if part:
        heading += f"（{part}）"
    overview = f"本卡 {len(jobs)} 个相关项目"
    if checked is not None:
        overview = f"检查 {checked} 个项目 · " + overview
    elements = [{"tag": "div", "text": {"tag": "lark_md", "content": overview}}]
    for number, job in enumerate(jobs, 1):
        if number > 1:
            elements.append({"tag": "hr"})
        analysis = job.get("analysis", {})
        title = re.sub(r"[「」]", "", job["title"])
        title = re.sub(r"专家\s*[-—]+\s*", " · ", title)
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content":
            f"**{number}. {brief(title, 65)}**\n{brief(recommendation(job), 65)}"}})
        elements.append({"tag": "div", "fields": [
            {"is_short": True, "text": {"tag": "lark_md", "content": "**💰 报酬**\n" + brief(pay_text(job), 55)}},
            {"is_short": True, "text": {"tag": "lark_md", "content": "**⏰ 截止**\n" + brief(deadline_text(job), 55)}}]})
        lines = ["**工作**　" + brief(summarize(job)),
                 "**推荐**　" + brief(analysis.get("fit_reason") or "、".join(job.get("reasons", [])) or "方向相关，需核对资历"),
                 "**门槛**　" + brief(analysis.get("requirements") or job.get("qualification") or "请查看项目详情")]
        if analysis:
            lines.append("**AI辅助**　" + brief(analysis.get("ai_steps")))
            lines.append("**注意**　" + brief(analysis.get("risks")))
        else:
            lines.append("**AI辅助**　" + brief(ai_workflow(job)))
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})
        url = job.get("url", "")
        if urlsplit(url).scheme == "https":
            label = "前往项目广场" if "corexpertdata.com" in url else "查看岗位详情"
            elements.append({"tag": "action", "actions": [{"tag": "button", "text": {
                "tag": "plain_text", "content": label}, "url": url, "type": "default"}]})
    if not jobs:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "今天暂无新的匹配机会。"}})
    failures = [status.split(":", 1)[0] for status in statuses if "采集失败" in status]
    if failures:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "⚠️ 检查失败　" + brief("、".join(failures), 150)}})
    analyzed = sum(bool(job.get("analysis")) for job in jobs)
    note = f"AI分析 {analyzed}/{len(jobs)} · 未分析项为规则初筛 · 未核实资历最高4星\nAI使用需获平台许可，专业交付由你复核。"
    if jobs and any("corexpertdata.com" in job.get("url", "") for job in jobs):
        note += "在项目广场按标题搜索。"
    note += f"\nAI Expert Job Radar v{__version__}"
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": note}]})
    return {"msg_type": "interactive", "card": {"config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": heading}, "template": "blue"},
        "elements": elements}}
