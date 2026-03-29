from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db  # Removed the dot so it works in the root folder

app = FastAPI()

# This allows your React frontend to talk to this Python backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Volunteer(BaseModel):
    name: str
    email: str

@app.get("/api")
def read_root():
    return {"status": "Backend is running on Vercel"}

@app.post("/api/add-volunteer")
async def add_volunteer(volunteer: Volunteer):
    try:
        # Saving to your Firebase collection
        doc_ref = db.collection("registrations_requests").document()
        doc_ref.set({
            "name": volunteer.name,
            "email": volunteer.email,
        })
        return {"message": "Volunteer added successfully!"}
    except Exception as e:
        return {"error": str(e)}, 500