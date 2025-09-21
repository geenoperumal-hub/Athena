# infrastructure/firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore

def init_firestore(credentials_path=None, project_id=None):
    if credentials_path:
        cred = credentials.Certificate(credentials_path)
    else:
        cred = credentials.ApplicationDefault()
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {'projectId': project_id})
    return firestore.client()
