from pathlib import Path

from papers_digest.settings import Settings, load_settings, save_settings


def test_settings_roundtrip(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "settings.json"
    monkeypatch.setenv("PAPERS_DIGEST_SETTINGS", str(path))

    save_settings(
        Settings(
            science_area="robotics",
            channel_id="@chan",
            post_time="09:30",
            use_llm=True,
            summarizer_provider="ollama",
        )
    )
    loaded = load_settings()

    assert loaded.science_area == "robotics"
    assert loaded.channel_id == "@chan"
    assert loaded.post_time == "09:30"
    assert loaded.use_llm is True
    assert loaded.summarizer_provider == "ollama"

