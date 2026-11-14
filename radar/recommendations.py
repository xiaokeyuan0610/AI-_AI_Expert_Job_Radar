DESIGN_TERMS = ("建筑", "室内", "空间设计", "空间规划", "景观", "城乡规划", "风景园林",
                "bim", "revit", "sketchup", "rhino", "autocad")
VISUAL_TERMS = ("影视", "摄影", "视觉", "美学", "图像", "视频", "媒体", "文化", "娱乐",
                "工业设计", "ui/ux", "blender", "3d美术", "文生图", "text-to-image", "图片标注", "图片质量")
from .details import deadline_at


def contains(text, terms):
    return any(term in text.lower() for term in terms)


def recommendation(job):
    direct = contains(job["title"], DESIGN_TERMS + VISUAL_TERMS)
    analysis = job.get("analysis", {})
    direction = round(analysis["fit_score"] * 0.4) if analysis else (40 if direct else 25)
    qualification = 25 if job.get("qualification_confirmed") is True else 10
    pay = 15 if job.get("salary") and "未注明" not in job["salary"] else 6
    timing = 10 if deadline_at(job) else 4
    assistance = 10 if analysis.get("ai_permission") == "allowed" else 4
    if analysis.get("ai_permission") == "prohibited":
        assistance = 0
    total = direction + qualification + pay + timing + assistance
    stars = 5 if total >= 85 else 4 if total >= 60 else 3 if total >= 45 else 2 if total >= 25 else 1
    if job.get("qualification_confirmed") is not True:
        stars = min(stars, 4)
    if job.get("qualification_confirmed") is False:
        stars = 2
    label = "资历已核对" if job.get("qualification_confirmed") is True else "资历待核对"
    return "★" * stars + "☆" * (5 - stars) + f" {total}分 · " + label


def ai_workflow(job):
    analysis = job.get("analysis")
    if analysis:
        if analysis["ai_permission"] == "prohibited":
            return "原文限制AI使用。按平台要求人工完成。"
        return analysis["ai_steps"] + " 人工复核　" + analysis["human_review"] + (
            " 使用前需确认平台许可。" if analysis["ai_permission"] == "unknown" else "")
    text = job["title"] + " " + job.get("description", "")
    if contains(text, DESIGN_TERMS):
        return "辅助整理需求与图纸资料、草拟方案对比和检查表。你核验尺寸、规范与专业结论。需平台允许。"
    if contains(text, VISUAL_TERMS):
        return "辅助整理素材、分镜与评测维度，形成问题清单。你复核视觉判断与版权授权。需平台允许。"
    return "辅助拆分任务、整理脱敏材料、草拟Rubric并检查格式。你核验专业事实和最终交付。需平台允许。"
