from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db

app = FastAPI()

# This is the "Permission Slip" (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows your localhost to talk to Render
    allow_methods=["*"],
    allow_headers=["*"],
)

class Volunteer(BaseModel):
    name: str
    email: str

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/add-volunteer")
async def add_volunteer(volunteer: Volunteer):
    doc_ref = db.collection("volunteers").document()
    doc_ref.set({
        "name": volunteer.name,
        "email": volunteer.email
    })
    return {"message": "Volunteer added successfully!"}
