DESIGN_TERMS = ("建筑", "室内", "空间设计", "空间规划", "景观", "城乡规划", "风景园林",
                "bim", "revit", "sketchup", "rhino", "autocad")
VISUAL_TERMS = ("影视", "摄影", "视觉", "美学", "图像", "视频", "媒体", "文化", "娱乐",
                "工业设计", "ui/ux", "blender", "3d美术")


def contains(text, terms):
    return any(term in text.lower() for term in terms)


def recommendation(job):
    direct = contains(job["title"], DESIGN_TERMS + VISUAL_TERMS)
    stars = 4 if direct else 3
    if direct and job.get("qualification_confirmed") is True:
        stars = 5
    if job.get("qualification_confirmed") is False:
        stars = 2
    label = "资历已核对" if job.get("qualification_confirmed") is True else "资历待核对"
    return "★" * stars + "☆" * (5 - stars) + " " + label


def ai_workflow(job):
    text = job["title"] + " " + job.get("description", "")
    if contains(text, DESIGN_TERMS):
        return "辅助整理需求与图纸资料、草拟方案对比和检查表。你核验尺寸、规范与专业结论。需平台允许。"
    if contains(text, VISUAL_TERMS):
        return "辅助整理素材、分镜与评测维度，形成问题清单。你复核视觉判断与版权授权。需平台允许。"
    return "辅助拆分任务、整理脱敏材料、草拟Rubric并检查格式。你核验专业事实和最终交付。需平台允许。"
