import requests
import json
from pathlib import Path
from faster_whisper import WhisperModel

# Load model only when transcription is requested
_model=None

def get_model():
    global _model
    if _model is None:
        _model=WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"   
        )
    return _model

def transcribe_recording(file_path:str):
    """Transcribe an audio or video recording.
    Returns:
    A dictionary containing the language, duration, and timestamped transcription segments.
    """

    path=Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    model=get_model()
    segments,info=model.transcribe(
        str(path),
        beam_size=5,
        vad_filter=True
    )
    transcript=[]
    for segment in segments:
        transcript.append({
            "start":round(segment.start,2),
            "end":round(segment.end,2),
            "text":segment.text.strip()
        })
    
    return{
        "language":info.language,
        "duration":round(info.duration,2),
        "segments":transcript
    }

def format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"