from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db

app = FastAPI()

# This section tells Render to allow your computer (localhost) to connect
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

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/add-volunteer")
async def add_volunteer(volunteer: Volunteer):
    try:
        doc_ref = db.collection("registrations_requests").document()
        doc_ref.set({
            "name": volunteer.name,
            "email": volunteer.email
        })
        return {"message": "Success! Volunteer added."}
    except Exception as e:
        return {"error": str(e)}
