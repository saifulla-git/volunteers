from fastapi import FastAPI, Request
from .database import db
from pydantic import BaseModel

app = FastAPI()

class Volunteer(BaseModel):
    name: str
    email: str

@app.get("/api/index")
def read_root():
    return {"status": "Backend is running on Vercel"}

# --- NEW: This part sends the list to your Dashboard ---
@app.get("/api/volunteers")
def get_volunteers():
    try:
        docs = db.collection("registrations_requests").stream()
        volunteers = []
        for doc in docs:
            volunteers.append(doc.to_dict())
        return volunteers
    except Exception as e:
        return {"error": str(e)}, 500

# --- UPDATED: This part saves the registration ---
@app.post("/api/index")
async def add_volunteer(volunteer: Volunteer):
    try:
        doc_ref = db.collection("registrations_requests").document()
        doc_ref.set({
            "name": volunteer.name,
            "email": volunteer.email,
        })
        return {"message": "Success! Volunteer added."}
    except Exception as e:
        return {"error": str(e)}, 500