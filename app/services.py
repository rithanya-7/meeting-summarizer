import json
import os
import tempfile
from pathlib import Path

import requests
from faster_whisper import WhisperModel


# ---------------------------------------------------------
# OLLAMA SETTINGS
# ---------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3:latest"

# Whisper model:
# tiny  = fastest, lower accuracy
# base  = good balance
# small = better accuracy, slower
WHISPER_MODEL = "base"


# ---------------------------------------------------------
# WHISPER MODEL
# ---------------------------------------------------------

_whisper = None


def get_whisper_model():
    global _whisper

    if _whisper is None:
        print("Loading Whisper model...")

        _whisper = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded.")

    return _whisper


# ---------------------------------------------------------
# AUDIO → TRANSCRIPT
# ---------------------------------------------------------

def transcribe_audio(audio_bytes: bytes, filename: str) -> str:

    suffix = Path(filename).suffix or ".wav"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp:

        temp.write(audio_bytes)
        temp_path = temp.name

    try:

        model = get_whisper_model()

        print("Transcribing audio...")

        segments, info = model.transcribe(
            temp_path,
            beam_size=5
        )

        transcript_parts = []

        for segment in segments:
            text = segment.text.strip()

            if text:
                transcript_parts.append(text)

        transcript = " ".join(transcript_parts).strip()

        if not transcript:
            raise RuntimeError(
                "No speech could be detected in the recording."
            )

        print("Transcription completed.")

        return transcript

    finally:

        try:
            os.remove(temp_path)

        except OSError:
            pass


# ---------------------------------------------------------
# TRANSCRIPT → SUMMARY USING OLLAMA
# ---------------------------------------------------------

def summarize_transcript(transcript: str) -> dict:

    prompt = f"""
You are an AI meeting assistant.

Analyze the meeting transcript below and create useful,
professional meeting notes.

Return ONLY valid JSON.

The JSON must contain exactly these four fields:

{{
    "summary": "A concise summary of the meeting",
    "decisions": [],
    "action_items": [],
    "open_questions": []
}}

Rules:

1. SUMMARY
- Write 4 to 7 clear sentences.
- Explain the main topics discussed.
- Mention important outcomes.
- Do not add information that is not in the transcript.

2. DECISIONS
- List the important decisions made during the meeting.
- Each decision should be a short sentence.
- If there are no decisions, return an empty list.

3. ACTION ITEMS
Each action item must be an object in this format:

{{
    "task": "Task that needs to be completed",
    "owner": "Person responsible or Not specified",
    "due_date": "Deadline or Not specified"
}}

Do NOT invent an owner or deadline.

4. OPEN QUESTIONS
- List questions or issues that were left unresolved.
- If there are no open questions, return an empty list.

5. ACCURACY
- Do not hallucinate.
- Do not invent names.
- Do not invent dates.
- Do not invent tasks.
- Only use information from the transcript.

MEETING TRANSCRIPT:

{transcript}
"""

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional meeting assistant. "
                    "Create accurate and action-oriented meeting notes. "
                    "Return ONLY valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "stream": False,

        "format": "json",

        "options": {
            "temperature": 0.2
        }
    }

    print(f"Sending transcript to Ollama model: {OLLAMA_MODEL}")

    # -----------------------------------------------------
    # CHECK OLLAMA CONNECTION
    # -----------------------------------------------------

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )

    except requests.ConnectionError as exc:

        raise RuntimeError(
            "Could not connect to Ollama. "
            "Please make sure Ollama is running."
        ) from exc

    except requests.Timeout as exc:

        raise RuntimeError(
            "Ollama took too long to respond. "
            "Try a shorter recording."
        ) from exc

    except requests.RequestException as exc:

        raise RuntimeError(
            f"Could not connect to Ollama: {str(exc)}"
        ) from exc


    # -----------------------------------------------------
    # HANDLE OLLAMA ERRORS
    # -----------------------------------------------------

    if response.status_code != 200:

        try:
            error_data = response.json()
            error_message = error_data.get(
                "error",
                response.text
            )
        except Exception:
            error_message = response.text

        if "not found" in str(error_message).lower():

            raise RuntimeError(
                f"Ollama model '{OLLAMA_MODEL}' was not found. "
                f"Run: ollama pull {OLLAMA_MODEL}"
            )

        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: "
            f"{error_message}"
        )


    # -----------------------------------------------------
    # READ OLLAMA RESPONSE
    # -----------------------------------------------------

    try:

        data = response.json()

    except ValueError as exc:

        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from exc


    content = data.get(
        "message",
        {}
    ).get(
        "content",
        ""
    )


    if not content:

        raise RuntimeError(
            "Ollama returned an empty response."
        )


    # -----------------------------------------------------
    # PARSE JSON FROM LLAMA
    # -----------------------------------------------------

    try:

        result = json.loads(content)

    except json.JSONDecodeError:

        # Sometimes a model may wrap JSON in markdown.
        cleaned = content.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:

            result = json.loads(cleaned)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Llama returned a response that was not valid JSON."
            ) from exc


    # -----------------------------------------------------
    # NORMALIZE RESULT
    # -----------------------------------------------------

    summary = result.get(
        "summary",
        ""
    )

    decisions = result.get(
        "decisions",
        []
    )

    action_items = result.get(
        "action_items",
        []
    )

    open_questions = result.get(
        "open_questions",
        []
    )


    # Make sure lists are actually lists
    if not isinstance(decisions, list):
        decisions = [str(decisions)]

    if not isinstance(action_items, list):
        action_items = []

    if not isinstance(open_questions, list):
        open_questions = [str(open_questions)]


    # Make sure every action item has the expected fields
    cleaned_actions = []

    for item in action_items:

        if isinstance(item, dict):

            cleaned_actions.append({
                "task": item.get(
                    "task",
                    "Not specified"
                ),

                "owner": item.get(
                    "owner",
                    "Not specified"
                ),

                "due_date": item.get(
                    "due_date",
                    "Not specified"
                )
            })

        else:

            cleaned_actions.append({
                "task": str(item),
                "owner": "Not specified",
                "due_date": "Not specified"
            })


    print("Meeting summary generated successfully.")

    return {
        "summary": summary,
        "decisions": decisions,
        "action_items": cleaned_actions,
        "open_questions": open_questions
    }