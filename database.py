import firebase_admin
from firebase_admin import credentials, firestore

# This connects the Brain to your Firebase data
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
