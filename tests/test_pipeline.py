from unittest.mock import patch

import pytest

from calls import pipeline as p


def test_chunks_preserve_long_transcript():
    text = ("[00:01:00] Обсудили задачу.\n" * 4000) + "x" * 30000
    parts = p.chunks(text)
    assert "".join(parts) == text
    assert all(0 < len(part) <= 24000 for part in parts)


def test_resume_after_codex_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "DATA", tmp_path / "data")
    source = tmp_path / "meeting.mp4"
    source.write_bytes(b"fake recording")
    transcript = "[00:00:01–00:00:04] Анна подготовит макет к пятнице."
    with (
        patch.object(p, "extract_audio") as extract,
        patch.object(p, "transcribe", return_value=transcript) as asr,
    ):
        with patch.object(p, "codex", side_effect=RuntimeError("network")):
            with pytest.raises(RuntimeError, match="network"):
                p.process(source)
        with patch.object(
            p, "codex", return_value="## Саммари\nМакет.\n## Задачи по участникам\nАнна"
        ):
            result = p.process(source)
        assert extract.call_count == asr.call_count == 1
        assert transcript in result.read_text()
        assert len(list(result.parent.glob("*.md"))) == 1


def test_codex_error_never_publishes_report(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "DATA", tmp_path / "data")
    source = tmp_path / "meeting.wav"
    source.write_bytes(b"fake")
    with (
        patch.object(p, "extract_audio"),
        patch.object(p, "transcribe", return_value="text"),
        patch.object(p, "codex", side_effect=RuntimeError("failed")),
    ):
        with pytest.raises(RuntimeError):
            p.process(source)
    assert not list((tmp_path / "data" / "results").glob("*.md"))


def test_summary_cache_depends_on_context_and_model(tmp_path):
    with patch.object(p, "codex", return_value="## Саммари\nГотово") as invoke:
        for context, model in [
            ("Анна", "gpt-6-sol"),
            ("Анна", "gpt-6-sol"),
            ("Илья", "gpt-6-sol"),
            ("Илья", "other"),
        ]:
            p.summarize("hello", context, model, tmp_path, lambda _: None)
        assert invoke.call_count == 3


def test_media_conversion(tmp_path):
    import wave

    source, output = tmp_path / "source.wav", tmp_path / "audio.wav"
    with wave.open(str(source), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        f.writeframes(b"\0" * 44100 * 4)
    p.extract_audio(source, output)
    with wave.open(str(output)) as f:
        assert f.getnchannels() == 1
        assert f.getframerate() == 16000
        assert f.getnframes() == 16000


def test_bad_media(tmp_path):
    source = tmp_path / "broken.mp4"
    source.write_text("not video")
    with pytest.raises(RuntimeError, match="извлечь аудио"):
        p.extract_audio(source, tmp_path / "audio.wav")
