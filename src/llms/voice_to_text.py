from faster_whisper import WhisperModel

_model = None
_current_model_size = None

def _get_model(model_size="small"):
    global _model, _current_model_size
    if _model is None or _current_model_size != model_size:
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
        _current_model_size = model_size
    return _model


def transcribe(audio_path: str, language: str = None, model_size: str = "medium") -> dict:
    """
    Transcribe an audio file to text.

    Args:
        audio_path: Path to audio file (mp3, wav, mp4, webm, ogg, etc.)
        language: Language code e.g. "he" for Hebrew, "en" for English.
                  None = auto-detect (less accurate for non-English).
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
                    small+ recommended for Hebrew.

    Returns:
        { "text": str, "language": str, "duration": float }
    """
    model = _get_model(model_size)
    segments, info = model.transcribe(audio_path, beam_size=5, language=language)
    text = " ".join(segment.text.strip() for segment in segments)
    return {
        "text": text,
        "language": info.language,
        "duration": round(info.duration, 2)
    }
