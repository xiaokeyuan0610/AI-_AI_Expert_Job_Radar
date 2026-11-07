import argparse
import re
from . import __version__
from .corexpert import collect_corexpert
from .core import summarize
from .feishu import send


def suitability(job):
    title = job["title"]
    if any(term in title for term in ("金融", "医学", "医疗", "法律", "英语", "方言", "少儿", "数学")):
        return None
    text = title + " " + job["description"]
    directions = [label for label, terms in [
        ("影视与视觉内容", ("影视", "摄影", "视觉", "美学", "图像", "视频", "设计")),
        ("模型评测与评分标准", ("多模态", "rubric", "Rubric", "评分标准", "评价标准", "模型评测")),
        ("任务与环境设计", ("RL", "Environment", "Agent", "工作流")),
    ] if any(term in text for term in terms)]
    if directions:
        return "优先核对", "、".join(directions)
    if any(term in title for term in ("企业场景", "办公工具", "多职业")):
        return "可拓展", "可结合真实工作经验参与任务设计或成果评价"
    return None


def build_digest(jobs):
    selected = [(job, suitability(job)) for job in jobs]
    selected = [(job, fit) for job, fit in selected if fit]
    selected.sort(key=lambda item: item[1][0] != "优先核对")
    sections = [f"【CoreXpert 专项测试】AI Expert Job Radar v{__version__}",
                f"实时检查{len(jobs)}个项目，筛选{len(selected)}个相关机会。",
                "按你的影视视觉、模型评测、Rubric及任务环境方向初筛，资历尚待核对。"]
    for number, (job, fit) in enumerate(selected, 1):
        description = dict(job, description=job["description"].split(" 要求：", 1)[0])
        requirements = re.sub(r"\s+", " ", job.get("qualification", "")).strip()
        sections.append("\n".join(["", f"{number}. {job['title']}【{fit[0]}】",
            "做什么　" + summarize(description), "与你的关联　" + fit[1],
            "报酬　" + job["salary"], "门槛　" + (requirements[:130] or "请查看项目详情")
            + ("…" if len(requirements) > 130 else "")]))
    if not selected:
        sections.append("当前未筛出符合上述方向的项目。")
    sections.extend(["", "入口　https://www.corexpertdata.com/operation/s/recruitment-square",
                     "按项目标题在广场搜索。测试快照保留日常去重记录。"])
    return sections, selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    jobs = collect_corexpert({})
    sections, selected = build_digest(jobs)
    batches = []
    current = ""
    for section in sections:
        if len((current + "\n" + section).encode()) > 14000:
            batches.append(current)
            current = f"【CoreXpert 专项测试续篇】v{__version__}\n" + section
        else:
            current += ("\n" if current else "") + section
    batches.append(current)
    for text in batches:
        if args.send:
            send({"msg_type": "text", "content": {"text": text}})
    print(f"Checked {len(jobs)} jobs; selected {len(selected)}; sent {len(batches) if args.send else 0} messages.")
    for job, fit in selected:
        print(job["title"], fit[0], job["salary"])


if __name__ == "__main__":
    main()
