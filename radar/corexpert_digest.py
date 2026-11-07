import argparse
import re
from . import __version__
from .corexpert import collect_corexpert
from .core import summarize
from .feishu import send
from .recommendations import DESIGN_TERMS, VISUAL_TERMS, contains, recommendation, ai_workflow
from .details import pay_text, deadline_text
from .ai_analysis import enrich_jobs
from .cards import card_message


def suitability(job):
    title = job["title"]
    if any(term in title for term in ("金融", "医学", "医疗", "法律", "英语", "方言", "少儿", "数学")):
        return None
    if contains(title, DESIGN_TERMS):
        return "优先核对", "建筑、空间或室内设计方向，可结合专业经历评估"
    if contains(title, VISUAL_TERMS):
        return "优先核对", "影视视觉、数字内容或设计类专业任务"
    if "多学科" in title and any(term in job.get("qualification", job["description"])
                                 for term in ("视觉传达", "工业设计", "影视", "建筑", "室内", "城乡规划", "风景园林")):
        return "优先核对", "招募专业包含视觉、建筑或设计方向，需要核对学历背景"
    if any(term in title for term in ("企业场景", "办公工具", "多职业")):
        return "可拓展", "可结合真实工作经验参与任务设计或成果评价"
    return None


def build_digest(jobs):
    selected = [(job, suitability(job)) for job in jobs]
    selected = [(job, fit) for job, fit in selected if fit]
    selected.sort(key=lambda item: item[1][0] != "优先核对")
    sections = [f"【CoreXpert 专项测试·筛选校正版】AI Expert Job Radar v{__version__}",
                f"实时检查{len(jobs)}个项目，筛选{len(selected)}个相关机会。",
                "按建筑空间室内设计、影视视觉、模型评测及任务环境方向初筛。",
                "星级综合方向、资格、报酬及期限信息。未知资历最高4星。"]
    for number, (job, fit) in enumerate(selected, 1):
        description = dict(job, description=job["description"].split(" 要求：", 1)[0])
        requirements = re.sub(r"\s+", " ", job.get("qualification", "")).strip()
        sections.append("\n".join(["", f"{number}. {job['title']}【{fit[0]}】",
            recommendation(job),
            "做什么　" + summarize(description), "与你的关联　" + fit[1],
            "报酬　" + pay_text(job), "截止　" + deadline_text(job),
            "门槛　" + (job.get("analysis", {}).get("requirements") or requirements[:130] or "请查看项目详情")
            + ("…" if len(requirements) > 130 else ""), "AI参与　" + ai_workflow(job)]))
        if job.get("analysis"):
            analysis = job["analysis"]
            sections.append("\n".join(["推荐理由　" + analysis["fit_reason"],
                "交付物　" + analysis["deliverables"], "注意　" + analysis["risks"]]))
        sections.append(job.get("analysis_status", "规则初筛"))
    if not selected:
        sections.append("当前未筛出符合上述方向的项目。")
    sections.extend(["", "入口　https://www.corexpertdata.com/operation/s/recruitment-square",
                     "按项目标题在广场搜索。测试快照保留日常去重记录。"])
    return sections, selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--require-ai", action="store_true")
    args = parser.parse_args()
    jobs = collect_corexpert({})
    enriched = enrich_jobs([job for job in jobs if suitability(job)])
    if args.require_ai and (not enriched or any(not job.get("analysis") for job in enriched)):
        raise RuntimeError("AI validation incomplete; no Feishu test sent")
    analyzed = {job["source_id"]: job for job in enriched}
    jobs = [analyzed.get(job["source_id"], job) for job in jobs]
    sections, selected = build_digest(jobs)
    cards = [dict(job, platform_name="CoreXpert", url=job.get("url") or
                  "https://www.corexpertdata.com/operation/s/recruitment-square") for job, _ in selected]
    batches = [cards[start:start + 3] for start in range(0, len(cards), 3)] or [[]]
    for index, batch in enumerate(batches, 1):
        if args.send:
            send(card_message(batch, test=True, checked=len(jobs), part=f"{index}/{len(batches)}"))
    print(f"Checked {len(jobs)} jobs; selected {len(selected)}; sent {len(batches) if args.send else 0} messages.")
    for job, fit in selected:
        print(job["title"], fit[0], job["salary"])


if __name__ == "__main__":
    main()
