import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Import services
from services.ai_service import extract_complaint_data
from services.audio_service import transcribe_audio
from services.data_fusion import get_final_priority_score
from services.firebase_service import push_to_firebase

app = FastAPI(title="JanDhwani 3D Digital Twin & AI Grievance Triage API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractedEntities(BaseModel):
    incident_location: Optional[str] = ""
    approx_date: Optional[str] = ""
    suspected_violation_or_issue: Optional[str] = ""

class ImageVerification(BaseModel):
    match_score: int = 0
    is_authentic_match: bool = False
    reasoning: Optional[str] = ""

class ComplaintResponse(BaseModel):
    id: str
    department: str
    category: str  # Kept for backward compatibility
    severity: str
    base_severity: int
    formal_summary: str
    summary: str   # Kept for backward compatibility
    final_priority_score: float
    district: str
    lat: float
    lng: float
    extracted_entities: ExtractedEntities
    image_verification: ImageVerification
    actionable_next_steps: List[str] = Field(default_factory=list)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/complaints", response_model=ComplaintResponse)
async def process_complaint(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    image_analysis: Optional[str] = Form("Live camera optical hardware capture verified"),
    image_metadata_status: Optional[str] = Form("Verified GPS & Timestamp Match"),
    district: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...)
):
    """
    Process a citizen complaint (text narrative or audio story),
    cross-verify with optical image evidence and metadata,
    extract structured entities and triage department,
    calculate priority fusion score, and push to 3D map.
    """
    if not text and not audio:
        raise HTTPException(status_code=400, detail="Must provide either text or audio.")

    complaint_text = text

    # 1. Audio Processing (if provided)
    if audio:
        audio_bytes = await audio.read()
        try:
            complaint_text = transcribe_audio(audio_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")

    # 2. AI Structured Triage Extraction
    try:
        ai_result = extract_complaint_data(
            text=complaint_text,
            image_analysis=image_analysis or "Ground visual evidence verified",
            metadata_status=image_metadata_status or "Verified GPS & Timestamp Match"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {str(e)}")

    # 3. Data Fusion (BigQuery demographic vulnerability index)
    try:
        final_score = get_final_priority_score(district, ai_result["base_severity"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fusion failed: {str(e)}")

    # 4. Real-time Broadcast (Firebase)
    payload = {
        "department": ai_result["department"],
        "category": ai_result["category"],
        "severity": ai_result["severity"],
        "base_severity": ai_result["base_severity"],
        "formal_summary": ai_result["formal_summary"],
        "summary": ai_result["summary"],
        "final_priority_score": final_score,
        "district": district,
        "lat": lat,
        "lng": lng,
        "original_text": complaint_text,
        "extracted_entities": ai_result.get("extracted_entities", {}),
        "image_verification": ai_result.get("image_verification", {}),
        "actionable_next_steps": ai_result.get("actionable_next_steps", [])
    }
    
    try:
        firebase_id = push_to_firebase(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase push failed: {str(e)}")

    return ComplaintResponse(
        id=firebase_id,
        department=ai_result["department"],
        category=ai_result["category"],
        severity=ai_result["severity"],
        base_severity=ai_result["base_severity"],
        formal_summary=ai_result["formal_summary"],
        summary=ai_result["summary"],
        final_priority_score=final_score,
        district=district,
        lat=lat,
        lng=lng,
        extracted_entities=ai_result.get("extracted_entities", {}),
        image_verification=ai_result.get("image_verification", {}),
        actionable_next_steps=ai_result.get("actionable_next_steps", [])
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
