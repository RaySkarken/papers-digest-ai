from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Settings:
    science_area: str = ""
    channel_id: str = ""
    post_time: str = ""
    use_llm: bool = False


def _settings_path() -> Path:
    path = os.getenv("PAPERS_DIGEST_SETTINGS", "data/settings.json")
    return Path(path)


def load_settings() -> Settings:
    path = _settings_path()
    if not path.exists():
        return Settings()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Settings(
        science_area=data.get("science_area", ""),
        channel_id=data.get("channel_id", ""),
        post_time=data.get("post_time", ""),
        use_llm=bool(data.get("use_llm", False)),
    )


def save_settings(settings: Settings) -> None:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), ensure_ascii=True, indent=2), encoding="utf-8")

