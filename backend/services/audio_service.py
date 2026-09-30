import os

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

def transcribe_audio(audio_content: bytes) -> str:
    """
    Transcribes audio using Google Cloud Speech-to-Text API.
    Utilizes the Chirp model optimized for regional Indian languages if available/configured.
    """
    if MOCK_MODE:
        print("[MOCK] Simulating audio transcription...")
        return "This is a mock transcribed text from audio."

    from google.cloud import speech

    # Instantiate a client
    client = speech.SpeechClient()

    # The audio content to transcribe
    audio = speech.RecognitionAudio(content=audio_content)

    # Configure recognition (using standard model here; adjust to 'chirp' if enabled in project)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="hi-IN", # Can be set dynamically based on user selection or auto-detected
        alternative_language_codes=["mr-IN", "ta-IN", "bn-IN", "te-IN"],
        model="latest_short", # Use 'chirp' if available in the GCP project region
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    transcript = []
    for result in response.results:
        transcript.append(result.alternatives[0].transcript)
        
    return " ".join(transcript)
