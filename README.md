# Meeting Summarizer

A small web application that turns a meeting audio file into a transcript, a short summary, key decisions, and action items.

## What it does

1. Upload a meeting audio file.
2. Send the audio to an ASR service for transcription.
3. Send the transcript to an LLM.
4. Generate a summary, key decisions, action items, and open questions.
5. Save the result in SQLite.
6. View previous meetings in the browser.

## Tech stack

- Python
- FastAPI
- SQLite + SQLAlchemy
- Faster-Whisper for local speech-to-text
- Ollama + Llama 3.2 for local LLM summarization
- HTML/CSS/JavaScript frontend

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your OpenAI API key.

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## API

- `POST /meetings` — upload and process a meeting
- `GET /meetings` — list saved meetings
- `GET /meetings/{meeting_id}` — retrieve one meeting

## LLM approach

The prompt asks for structured JSON containing a concise summary, important decisions, action items with task/owner/due date, and unresolved questions. It also explicitly tells the model not to invent missing owners or dates. This makes the output more useful than a generic paragraph summary.

## Demo video

Show the upload, processing, transcript, summary, decisions, action items, and saved meeting history.

## Testing

```bash
pytest
```

Do not commit `.env` or your API key to GitHub.
