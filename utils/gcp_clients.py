# utils/gcp_clients.py

from google.cloud import bigquery, firestore, storage

class GCPClients:
    def __init__(self, project_id, region="us-central1"):
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.storage_client = storage.Client(project=project_id)
        self.firestore_client = firestore.Client(project=project_id)

    def get_bigquery_client(self):
        return self.bq_client

    def get_storage_client(self):
        return self.storage_client

    def get_firestore_client(self):
        return self.firestore_client
