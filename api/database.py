import os
import firebase_admin
from firebase_admin import credentials, firestore

# This tells Vercel exactly where to find the file, no guessing.
current_dir = os.path.dirname(os.path.abspath(__file__))
firebase_key_path = os.path.join(current_dir, "firebase.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()