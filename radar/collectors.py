import json
from pathlib import Path
from typing import Protocol


class Collector(Protocol):
    def collect(self, platform: dict) -> list[dict]: ...


class LocalJsonCollector:
    def collect(self, platform):
        rows = json.loads(Path(platform["path"]).read_text(encoding="utf-8"))
        for row in rows:
            if not all(isinstance(row.get(key), str) and row[key].strip()
                       for key in ("title", "url", "description")):
                raise ValueError("Invalid job record")
            if not row["url"].startswith("https://"):
                raise ValueError("Job URL must use HTTPS")
        return rows


def collect(platform):
    if platform["method"] == "corexpert_session":
        from .corexpert import collect_corexpert
        return collect_corexpert(platform)
    if platform["method"] == "tencent_session":
        from .tencent import collect_tencent
        return collect_tencent(platform)
    if platform["method"] in {"appen_public", "talents_public", "fellow_public"}:
        from .public_sources import collect_public
        return collect_public(platform)
    if platform["method"] == "bencher_public":
        from .bencher import collect_bencher
        return collect_bencher(platform)
    if platform["method"] == "local_json":
        return LocalJsonCollector().collect(platform)
    raise ValueError("Platform adapter not yet reviewed or implemented")

