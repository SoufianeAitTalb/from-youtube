from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api import router as api_router

app = FastAPI(title="YouTube Video Processing API")

# Mount static files
app.mount("/outputs", StaticFiles(directory="processing_output"), name="outputs")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to YouTube Processing API"}

@app.get("/most-replayed")
def get_most_replayed_proxy(videoId: str, numberOfParts: int = 3):
    """
    Proxy or Mock for the get_replayed_parts logic.
    In a real scenario, this might call an external service or use internal logic.
    For this assignment, we'll return mock data or reuse replayed_parts.py logic if feasible.
    """
    # Attempt to use real logic if possible, otherwise mock
    try:
        from replayed_parts import get_replayed_parts
        # Note: replayed_parts.py currently calls localhost:8000, avoiding recursion loop is needed.
        # IF replayed_parts.py CLIENT logic is just a wrapper around an API call, we need the SERVER side logic.
        # Since the user prompt says: "1) Get Most Replayed Parts (calls backend): GET http://localhost:8000/most-replayed"
        # It implies WE are implementing this endpoint.
        # But `replayed_parts.py` provided by user calls THIS endpoint. 
        # So we need the actual implementation of how to get replayed parts from YT.
        # Since we don't have that library code (it might be in `replayed_parts.py` but that file calls localhost),
        # checking `replayed_parts.py` again... it does `requests.get(url)`.
        # This implies there was ALREADY a server running or we need to simulate yt-dlp/similar extraction.
        #
        # User prompt says: "Implement an API layer ... Also provide a minimal FastAPI backend skeleton ... demonstrating the endpoints"
        # I will return MOCK data for now as I don't have the internal youtube-replayed-parts extraction logic.
        pass
    except ImportError:
        pass

    # Mock Response based on User Request description
    return {
        "replayedParts": [
            {"start": 30, "end": 45, "position": 1, "duration": 15},
            {"start": 120, "end": 140, "position": 2, "duration": 20},
            {"start": 300, "end": 310, "position": 3, "duration": 10},
        ]
    }
