import os
import json

# Mock mode for testing without GCP credentials
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

SEVERITY_NUMERIC_MAP = {
    "low": 3,
    "medium": 6,
    "high": 8,
    "critical": 10
}

VISION_VALIDATION_SYSTEM_PROMPT = """
You are an uncompromising, highly rigorous Fraud Detection and Image Forensics AI officer for a government civic grievance portal. Your job is to audit citizen-submitted evidence photos against their text complaints.

### Core Directive:
Analyze the provided image and the text description of the grievance. You must rigorously verify if the visual evidence directly matches the physical problem claimed in the story. 

### Strict Failure Rules (Zero Tolerance):
1. **Unrelated Objects:** If the image shows indoor household items (e.g., curtains, walls, furniture, ceilings), selfies, random screenshots, or objects completely unrelated to the civic complaint, you MUST set `is_authentic_match` to `false` and `match_score` to `0`.
2. **Context Mismatch:** If the complaint is about "garbage/solid waste dump" but the photo shows an indoor room or a clean street, it is a mismatch. 
3. Do not try to be overly accommodating. If there is doubt, fail it. Government resources depend on your accuracy.

### Required JSON Output Schema:
{
  "formal_summary": "Objective 1-2 sentence bureaucratic summary of the issue.",
  "department": "Target department routing (e.g., Municipal Corporation, Public Works, FDA)",
  "severity_level": "Low / Medium / High / Critical",
  "image_match_score": <Integer between 0 and 100>,
  "is_authentic_match": <Boolean: true or false>,
  "verification_reasoning": "Detailed forensic explanation. State clearly what is actually visible in the photo and why it matches or fails to match the reported complaint story."
}
"""

TRIAGE_PROMPT_TEMPLATE = """You are an expert AI triage officer for a government public grievance and consumer protection cell (similar to the FDA and CPGRAMS portal). 

Your task is to analyze a citizen's complaint, which includes a narrative written in a raw, story-like format, and metadata about an attached evidence image.

### Input Data:
- Citizen's Raw Story: "{USER_COMPLAINT_STORY}"
- Image Description / OCR Text extracted from Photo: "{IMAGE_ANALYSIS_OR_OCR}"
- Image Metadata (Timestamp/GPS match status): "{IMAGE_METADATA_STATUS}"

### Instructions:
1. Summarize the core grievance objectively into a clear, professional bureaucratic summary (max 2 sentences).
2. Extract key structured entities required for government action.
3. Perform a rigorous forensic cross-verification check: Does the evidence image directly support and match the narrative described in the citizen's story?
   - Apply Zero Tolerance Failure Rules: If image contains indoor household items (curtains, walls, furniture, ceilings), selfies, random screenshots, or clean street when reporting garbage, set `is_authentic_match` to `false` and `match_score` to `0`.
4. Classify the severity level (Low, Medium, High, Critical).
5. Suggest the correct government department to route this to (e.g., Food and Drug Administration, Municipal Corporation, Public Works Department, Police).

### Output Format:
Return your response strictly in valid JSON format using the following keys:
{{
  "department": "",
  "severity": "Low | Medium | High | Critical",
  "formal_summary": "",
  "extracted_entities": {{
    "incident_location": "",
    "approx_date": "",
    "suspected_violation_or_issue": ""
  }},
  "image_verification": {{
    "match_score": 0,
    "is_authentic_match": true,
    "reasoning": ""
  }},
  "actionable_next_steps": []
}}
"""

def extract_complaint_data(
    text: str,
    image_analysis: str = "Live camera hardware optical capture verified",
    metadata_status: str = "Verified GPS & Timestamp Match"
) -> dict:
    """
    Analyzes citizen feedback story, cross-verifies with image evidence & metadata,
    classifies into a government department, extracts structured entities,
    and assigns severity scores.
    """
    if MOCK_MODE:
        lower = text.lower()
        img_lower = (image_analysis or "").lower()

        # Zero-Tolerance Fraud Audit 1: Solid Black / Pitch Dark / Blank / Obstructed Lens Photo
        is_black_fraud = any(w in img_lower for w in [
            "black", "dark", "blank", "solid black", "pitch black", "obscured", "lens cap", "covered"
        ]) or any(w in lower for w in ["black photo", "black image", "blank photo", "dark photo"])

        if is_black_fraud:
            dept = "Municipal Corporation / Fraud Audit Cell"
            sev = "Low"
            summary = "Grievance flagged for rejection: Submitted evidence photo is completely black/blank or lens obstructed with zero optical detail."
            issue = "Obstructed lens / Solid black evidence"
            base_sev = 0

            return {
                "department": dept,
                "category": dept,
                "severity": sev,
                "base_severity": base_sev,
                "formal_summary": summary,
                "summary": summary,
                "extracted_entities": {
                    "incident_location": "Unverified - Black Image",
                    "approx_date": "N/A",
                    "suspected_violation_or_issue": issue
                },
                "image_verification": {
                    "match_score": 0,
                    "is_authentic_match": False,
                    "reasoning": "Zero Tolerance Fraud Failure (Match Score: 0%): Submitted photo is completely black/dark with zero optical incident detail."
                },
                "actionable_next_steps": [
                    "Reject grievance submission due to solid black/blank evidence photo",
                    "Notify citizen to re-upload clear illuminated photo of reported issue"
                ]
            }

        # Zero-Tolerance Fraud Audit 2: Check for indoor household items (curtains, walls, furniture, sofa, ceiling, room, selfie, etc.)
        is_indoor_fraud = any(w in img_lower for w in [
            "curtain", "indoor", "room", "wall", "ceiling", "furniture", "sofa", "bed", "selfie", "decor", "fabric", "reject"
        ]) or any(w in lower for w in ["curtain", "indoor furniture", "curtains"])

        if is_indoor_fraud:
            dept = "Municipal Corporation / Fraud Audit Cell"
            sev = "Low"
            summary = "Grievance flagged for rejection: Submitted evidence photo depicts indoor household items (curtains/furniture/walls) unrelated to reported outdoor civic issue."
            issue = "Unrelated optical evidence / Fraud audit failure"
            base_sev = 0

            return {
                "department": dept,
                "category": dept,
                "severity": sev,
                "base_severity": base_sev,
                "formal_summary": summary,
                "summary": summary,
                "extracted_entities": {
                    "incident_location": "Unverified - Evidence Mismatch",
                    "approx_date": "N/A",
                    "suspected_violation_or_issue": issue
                },
                "image_verification": {
                    "match_score": 0,
                    "is_authentic_match": False,
                    "reasoning": "Zero Tolerance Fraud Failure (Match Score: 0%): Submitted photo depicts indoor household items (curtains/furniture/walls) completely unrelated to reported outdoor civic complaint."
                },
                "actionable_next_steps": [
                    "Reject grievance submission due to invalid/unrelated evidence photo",
                    "Notify citizen to re-upload clear on-ground evidence photo of reported issue"
                ]
            }

        if any(w in lower for w in ["food", "milk", "expiry", "dairy", "medicine", "adulterat", "ration", "fssai"]):
            dept = "Food and Drug Administration (FDA) & Consumer Protection"
            sev = "High"
            summary = "Grievance alleging supply/sale of adulterated, expired perishable goods or compromised medical supplies."
            issue = "Suspected consumer health violation / adulterated products"
        elif any(w in lower for w in ["water", "pipe", "jal", "leak", "sewage", "drain"]):
            dept = "Ministry of Jal Shakti / Municipal Water Board"
            sev = "High"
            summary = "Critical disruption in civic water supply line with contamination hazard and local road flooding."
            issue = "Water distribution pipe rupture / civic line compromise"
        elif any(w in lower for w in ["road", "pothole", "asphalt", "bridge", "highway", "traffic"]):
            dept = "Public Works Department (PWD) / Ministry of Road Transport"
            sev = "Medium"
            summary = "Severe roadway cavity and structural asphalt hazard creating vehicular safety risk."
            issue = "Road surface deformation / hazardous pothole"
        elif any(w in lower for w in ["power", "electric", "transformer", "wire", "current"]):
            dept = "Ministry of Power / State Electricity Distribution"
            sev = "Critical"
            summary = "High-voltage electrical hazard with exposed wire / transformer failure posing danger to residents."
            issue = "Uninsulated electrical hazard"
        else:
            dept = "Municipal Corporation / Public Grievance Cell"
            sev = "Medium"
            summary = f"Citizen civic grievance logged for administrative intervention: {text[:100]}..."
            issue = "Civic amenities deficit"

        base_sev = SEVERITY_NUMERIC_MAP.get(sev.lower(), 7)
        dynamic_score = 75 + ((len(text) + len(image_analysis or '')) % 19)

        return {
            "department": dept,
            "category": dept,
            "severity": sev,
            "base_severity": base_sev,
            "formal_summary": summary,
            "summary": summary,
            "extracted_entities": {
                "incident_location": "Hyper-local coordinates verified via GPS fix",
                "approx_date": "Recent incident",
                "suspected_violation_or_issue": issue
            },
            "image_verification": {
                "match_score": dynamic_score,
                "is_authentic_match": True,
                "reasoning": f"Optical evidence matches reported {issue} with {dynamic_score}% confidence. Geolocation coordinates cross-verified with submission node."
            },
            "actionable_next_steps": [
                f"Dispatch inspection team from {dept}",
                "Register verified ticket on National CPGRAMS & 3D Spatial Twin",
                "Notify ward supervisor and nodal redressal engineer"
            ]
        }

    # Initialize Vertex AI
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel

    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is missing.")

    aiplatform.init(project=project_id, location=location)
    
    model = GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    prompt = TRIAGE_PROMPT_TEMPLATE.format(
        USER_COMPLAINT_STORY=text,
        IMAGE_ANALYSIS_OR_OCR=image_analysis,
        IMAGE_METADATA_STATUS=metadata_status
    )
    
    response = model.generate_content(prompt)
    
    try:
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        elif result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        data = json.loads(result_text.strip())
        
        # Populate backward-compatible keys and numeric base_severity
        data["category"] = data.get("department", "General Grievance")
        data["summary"] = data.get("formal_summary", text[:120])
        sev_str = str(data.get("severity", "Medium")).lower()
        data["base_severity"] = SEVERITY_NUMERIC_MAP.get(sev_str, 6)
        
        return data
    except json.JSONDecodeError:
        raise ValueError("Failed to parse Gemini response as JSON.")


if __name__ == "__main__":
    sample_story = (
        "Yesterday around 2 PM near Sector 14 market in Gurgaon, I bought a packet of milk from Sharma General Store. "
        "When I came home and opened it, it smelled sour and curdled immediately upon boiling. The batch number is B-402 and best before date was 3 days ago!"
    )
    sample_ocr = "Photo of a milk packet showing brand logo, Batch B-402, and Expiry Date: 27/09/2026 printed on packaging."
    sample_meta = "Verified GPS (Gurgaon Sector 14) & Timestamp (2026-09-30) Match"

    print("Executing JanDhwani AI Triage Officer Service...")
    res = extract_complaint_data(
        text=sample_story,
        image_analysis=sample_ocr,
        metadata_status=sample_meta
    )
    print("\n=== AI Triage Officer Analysis Output JSON ===")
    print(json.dumps(res, indent=2))

