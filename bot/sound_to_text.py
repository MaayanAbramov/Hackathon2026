from faster_whisper import WhisperModel

_model = None


def _get_model(model_size="base"):
    global _model
    if _model is None:
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str, model_size: str = "base") -> dict:
    """
    Transcribe an audio file to text.

    Args:
        audio_path: Path to audio file (mp3, wav, mp4, webm, ogg, etc.)
        model_size: Whisper model size (tiny, base, small, medium, large-v3)

    Returns:
        { "text": str, "language": str, "duration": float }
    """
    model = _get_model(model_size)
    segments, info = model.transcribe(audio_path, beam_size=5, language="he")
    text = " ".join(segment.text.strip() for segment in segments)
    return {
        "text": text,
        "language": info.language,
        "duration": round(info.duration, 2)
    }