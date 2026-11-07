"""Manual connectivity check using synthetic job data, without Feishu delivery."""
from .ai_analysis import enrich_jobs


def main():
    results = enrich_jobs([{
        "title": "建筑空间图像评测（虚构测试数据）",
        "description": "检查室内空间图像的构图、尺度与材质，交付评分及理由。",
    }])
    if not results[0].get("analysis"):
        raise RuntimeError("AI connectivity test failed; no Feishu message sent")
    print("AI connectivity test passed using synthetic job data.")


if __name__ == "__main__":
    main()
