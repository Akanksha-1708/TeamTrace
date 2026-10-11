
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from faster_whisper import WhisperModel

# Load environment variables from the project's .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Whisper transcription model
_model = None


def get_model():
    """Load the Whisper model once and reuse it."""
    global _model

    if _model is None:
        _model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
        )

    return _model


def transcribe_recording(file_path: str) -> dict:
    """Transcribe an audio or video recording using Faster-Whisper."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Recording not found: {file_path}")

    model = get_model()

    segments, info = model.transcribe(
        str(path),
        beam_size=5,
        vad_filter=True,
    )

    transcript = []

    for segment in segments:
        transcript.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            }
        )

    return {
        "language": info.language,
        "duration": round(info.duration, 2),
        "segments": transcript,
    }


def format_timestamp(seconds: float) -> str:
    """Convert seconds into MM:SS format."""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    return f"{minutes:02d}:{remaining_seconds:02d}"


def analyze_meeting(transcript: str) -> dict:
    """Analyze a meeting transcript using the hosted Mistral API."""
    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY is missing. Add it to your project's .env file."
        )

    prompt = f"""
Analyze the meeting transcript below.

Extract:
1. A concise summary.
2. Main topics.
3. Tasks, including assignees and deadlines when mentioned.
4. Decisions made.
5. Unresolved questions.

Return a JSON object with exactly these keys:
- summary: string
- topics: array of strings
- tasks: array of objects containing task, assignee, deadline
- decisions: array of strings
- questions: array of strings

Use null for an unknown assignee or deadline.
Do not invent information. Return only valid JSON.

Meeting transcript:
{transcript}
"""

    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "mistral-small-latest",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a meeting intelligence assistant. "
                        "Analyze transcripts faithfully and return valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        },
        timeout=120,
    )

    # Raise a clear HTTP error if the API rejects the request.
    response.raise_for_status()

    response_data = response.json()
    choices = response_data.get("choices", [])

    if not choices:
        raise ValueError("Mistral returned no response choices.")

    content = choices[0].get("message", {}).get("content")

    if not content:
        raise ValueError("Mistral returned an empty response.")

    try:
        analysis = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("Mistral returned invalid JSON.") from error

    if not isinstance(analysis, dict):
        raise ValueError("Mistral response must be a JSON object.")

    required_keys = {
        "summary",
        "topics",
        "tasks",
        "decisions",
        "questions",
    }

    missing_keys = required_keys - analysis.keys()

    if missing_keys:
        raise ValueError(
            f"Mistral response is missing fields: {sorted(missing_keys)}"
        )

    return analysis


# SQLite database
DB_PATH = BASE_DIR / "teamtrace.db"


def get_db_connection():
    """Create a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """Create the meetings table if it does not exist."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                recording_name TEXT,
                transcript TEXT NOT NULL,
                analysis TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_meeting(title, recording_name, transcript, analysis):
    """Save a meeting and its analysis to SQLite."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO meetings (
                title,
                recording_name,
                transcript,
                analysis,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                recording_name,
                transcript,
                json.dumps(analysis, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        return cursor.lastrowid


def get_meetings():
    """Return saved meetings, newest first."""
    with get_db_connection() as conn:
        return conn.execute(
            """
            SELECT id, title, recording_name, created_at
            FROM meetings
            ORDER BY id DESC
            """
        ).fetchall()


def get_meeting(meeting_id):
    """Return a saved meeting by its ID."""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM meetings WHERE id = ?",
            (meeting_id,),
        ).fetchone()
