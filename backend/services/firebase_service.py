import os
import uuid
import time

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# Initialize Firebase only once
if not MOCK_MODE:
    try:
        import firebase_admin
        from firebase_admin import credentials, db
        # Assuming the service account key is available in the environment or file
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # Fallback to application default credentials if running in GCP
            cred = credentials.ApplicationDefault()
            
        database_url = os.getenv("FIREBASE_DATABASE_URL")
        if not database_url:
            raise ValueError("FIREBASE_DATABASE_URL environment variable is missing.")
            
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
    except Exception as e:
        print(f"Warning: Firebase initialization failed: {e}")

def push_to_firebase(payload: dict) -> str:
    """
    Pushes the finalized complaint payload to the Firebase Realtime Database.
    This triggers WebSockets for the frontend 3D map.
    """
    # Add metadata
    complaint_id = str(uuid.uuid4())
    payload["id"] = complaint_id
    payload["timestamp"] = int(time.time() * 1000)
    
    if MOCK_MODE:
        print(f"[MOCK] Pushing to Firebase Realtime Database (complaints/{complaint_id}):")
        print(payload)
        return complaint_id

    # Push to Realtime Database
    ref = db.reference('complaints')
    new_complaint_ref = ref.child(complaint_id)
    new_complaint_ref.set(payload)
    
    return complaint_id
