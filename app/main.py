import json
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Meeting
from .services import summarize_transcript, transcribe_audio

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Meeting Summarizer")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
MAX_FILE_SIZE = 25 * 1024 * 1024

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.post("/meetings")
async def create_meeting(file: UploadFile = File(...), db: Session = Depends(get_db)):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File is larger than the 25 MB limit.")
    try:
        transcript = transcribe_audio(audio_bytes, file.filename)
        result = summarize_transcript(transcript)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}")
    meeting = Meeting(
        filename=file.filename,
        transcript=transcript,
        summary=result["summary"],
        decisions=json.dumps(result["decisions"]),
        action_items=json.dumps(result["action_items"]),
        open_questions=json.dumps(result["open_questions"]),
    )
    db.add(meeting); db.commit(); db.refresh(meeting)
    return meeting_to_dict(meeting)

@app.get("/meetings")
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.id.desc()).all()
    return [meeting_to_dict(m, compact=True) for m in meetings]

@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return meeting_to_dict(meeting)

def meeting_to_dict(meeting: Meeting, compact: bool = False):
    result = {
        "id": meeting.id,
        "filename": meeting.filename,
        "summary": meeting.summary,
        "decisions": json.loads(meeting.decisions),
        "action_items": json.loads(meeting.action_items),
        "open_questions": json.loads(meeting.open_questions),
    }
    if not compact:
        result["transcript"] = meeting.transcript
    return result
