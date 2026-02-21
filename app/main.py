
from fastapi import FastAPI
import logging

# Simple standalone logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Secure Bloom SSE")

@app.get("/")
async def root():
    logger.info("SSE Server LIVE!")
    return {"message": "🚀 Secure Bloom SSE Working!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "ready": True}

@app.post("/patients")
async def create_patient():
    return {"patient_id": 1, "status": "would be encrypted"}

@app.get("/patients/search")
async def search(q: str = "test"):
    return [{"id": 1, "name": "John Doe (demo)"}]

@app.get("/patients/{id}")
async def get_patient(id: int):
    return {"id": id, "name": "John Doe", "status": "decrypted"}
