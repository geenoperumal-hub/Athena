# infrastructure/gcp_setup.py
import os
from google.cloud import aiplatform
from google.cloud import bigquery
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore

class GCPSetup:
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        
    def initialize_services(self):
        """Initialize all Google Cloud services"""
        # Vertex AI
        aiplatform.init(project=self.project_id, location=self.region)
        
        # BigQuery
        self.bq_client = bigquery.Client(project=self.project_id)
        
        # Cloud Storage
        self.storage_client = storage.Client(project=self.project_id)
        
        # Firebase
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': self.project_id
            })
        
        self.firestore_client = firestore.client()
        
        return {
            'bq_client': self.bq_client,
            'storage_client': self.storage_client,
            'firestore_client': self.firestore_client
        }
