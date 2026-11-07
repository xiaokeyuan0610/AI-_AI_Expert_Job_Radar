import argparse
import json
from pathlib import Path
from .collectors import collect
from .core import identity, message, score
from .feishu import send
from . import __version__


def run(config, rules, state_path, push=False, demo=False, test_send=False):
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() and not test_send else []
    seen = set(state)
    pending = {}
    statuses = []
    failed = False
    for platform in config:
        name = platform.get("name", platform["id"])
        if not platform.get("enabled"):
            statuses.append(name + ": " + platform.get("review_status", "待提供链接/审核接入"))
            continue
        try:
            rows = collect(platform)
            statuses.append(f"{name}: 读取 {len(rows)} 条")
            for row in rows:
                points, reasons = score(row, rules)
                key = identity(row)
                if points >= rules["threshold"] and key not in seen:
                    pending[key] = dict(row, score=points, reasons=reasons, platform_name=name)
        except Exception:
            failed = True
            statuses.append(name + ": 采集失败（不是无任务）")
    ordered = sorted(pending.items(), key=lambda item: (item[1]["platform_name"], -item[1]["score"]))
    batch_size = rules.get("batch_size", 10)
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    batches = []
    for entry in ordered:
        if (not batches or len(batches[-1]) >= batch_size
                or batches[-1][-1][1]["platform_name"] != entry[1]["platform_name"]):
            batches.append([])
        batches[-1].append(entry)
    batches = batches or [[]]
    for batch in batches:
        payload = message([row for _, row in batch], statuses, demo)
        if test_send:
            payload["content"]["text"] = payload["content"]["text"].replace(
                "新增匹配任务：", "当前相关任务：")
            payload["content"]["text"] = "【版本测试｜实时岗位快照】\n" + payload["content"]["text"]
        if push:
            send(payload)
            if test_send:
                continue
            seen.update(key for key, _ in batch)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = state_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(sorted(seen)), encoding="utf-8")
            temporary.replace(state_path)
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--test-send", action="store_true", help="Send real jobs without modifying daily delivery state")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    if args.demo and (args.send or args.test_send):
        parser.error("Demo data cannot be sent")
    config = json.loads(Path("config/platforms.json").read_text(encoding="utf-8"))
    if args.demo:
        config = [{"id": "demo", "enabled": True, "method": "local_json", "path": "examples/jobs.json"}]
    rules = json.loads(Path("config/matching.json").read_text(encoding="utf-8"))
    if args.send and not any(platform.get("enabled") for platform in config):
        parser.error("No enabled platforms; configure and review sources first")
    try:
        return run(config, rules, Path("state/sent.json"), args.send or args.test_send, args.demo, args.test_send)
    except Exception:
        print("Run failed; check configuration, credentials or network. Secrets omitted.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

