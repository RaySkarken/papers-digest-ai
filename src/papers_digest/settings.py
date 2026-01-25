from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict


@dataclass
class ChannelConfig:
    """Configuration for a single channel."""
    channel_id: str
    science_area: str = ""
    post_time: str = ""
    use_llm: bool = False
    summarizer_provider: str = "auto"
    enabled: bool = True


@dataclass
class Settings:
    """Global settings with multiple channel configurations."""
    channels: Dict[str, ChannelConfig] = field(default_factory=dict)
    # Legacy fields for backward compatibility
    science_area: str = ""
    channel_id: str = ""
    post_time: str = ""
    use_llm: bool = False
    summarizer_provider: str = "auto"


def _settings_path() -> Path:
    path = os.getenv("PAPERS_DIGEST_SETTINGS", "data/settings.json")
    return Path(path)


def load_settings() -> Settings:
    path = _settings_path()
    if not path.exists():
        return Settings()
    data = json.loads(path.read_text(encoding="utf-8"))
    
    # Load channels if they exist
    channels = {}
    if "channels" in data:
        for channel_id, channel_data in data["channels"].items():
            channels[channel_id] = ChannelConfig(**channel_data)
    
    # Legacy support: migrate old single channel to new format
    if not channels and data.get("channel_id"):
        channel_id = data["channel_id"]
        channels[channel_id] = ChannelConfig(
            channel_id=channel_id,
            science_area=data.get("science_area", ""),
            post_time=data.get("post_time", ""),
            use_llm=bool(data.get("use_llm", False)),
            summarizer_provider=data.get("summarizer_provider", "auto"),
        )
    
    return Settings(
        channels=channels,
        science_area=data.get("science_area", ""),
        channel_id=data.get("channel_id", ""),
        post_time=data.get("post_time", ""),
        use_llm=bool(data.get("use_llm", False)),
        summarizer_provider=data.get("summarizer_provider", "auto"),
    )


def save_settings(settings: Settings) -> None:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Convert channels dict to serializable format
    data = asdict(settings)
    data["channels"] = {k: asdict(v) for k, v in settings.channels.items()}
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def get_channel_config(settings: Settings, channel_id: str) -> ChannelConfig | None:
    """Get channel configuration, or None if not found."""
    return settings.channels.get(channel_id)


def add_channel(settings: Settings, channel_id: str, science_area: str = "") -> ChannelConfig:
    """Add or update a channel configuration."""
    if channel_id in settings.channels:
        config = settings.channels[channel_id]
        if science_area:
            config.science_area = science_area
    else:
        config = ChannelConfig(
            channel_id=channel_id,
            science_area=science_area,
            use_llm=settings.use_llm,
            summarizer_provider=settings.summarizer_provider,
        )
        settings.channels[channel_id] = config
    return config


def remove_channel(settings: Settings, channel_id: str) -> bool:
    """Remove a channel configuration. Returns True if removed."""
    if channel_id in settings.channels:
        del settings.channels[channel_id]
        return True
    return False

