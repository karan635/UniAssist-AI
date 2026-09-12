from fastapi import APIRouter, HTTPException, UploadFile, File

from app.services.voice.stt_service import STTService

router = APIRouter()


@router.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        service = STTService()
        result = service.transcribe(audio_bytes, filename=file.filename or "audio.wav")

        return result  # {"text": "...", "language": "en"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")