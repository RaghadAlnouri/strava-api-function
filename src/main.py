# Imports
import sys
import json
import gzip
import logging
import requests
import os
from google.cloud import bigquery       # see requirements.txt
from google.cloud import secretmanager  # see requirements.txt

# Global Variables 
# GCP related variables
# Requirements: Enable APIs & Create resources
# --------------------------------------
GCP_PROJECT_ID  = 'strava-d199d'   # GCP project id of the GCP resources
BQ_DATASET      = 'strava'          # your BigQuery Dataset used to store strava data 
BQ_TABLE        = 'activities'      # Big query table used to store strava data 

# Strava Variables
STORED_CLIENT       = 'strava_clientid'     # client id in Secret Manager as in secretmanager://projects/PROJECT_ID/secrets/
STORED_SECRET       = 'strava_clientsecret' # strava secret in Secret Manager as in secretmanager://projects/PROJECT_ID/secrets/
STORED_REFRESHTOKEN = 'strava_refreshtoken' # strava refresh token in Secret Manager as in secretmanager://projects/PROJECT_ID/secrets/
# --------------------------------------

# Logging level
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Function to retrieve a secret from Secret Manager
def fetch_from_secretmanager(project_id, secret_id):
    client      = secretmanager.SecretManagerServiceClient()
    name        = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response    = client.access_secret_version(request={"name": name})
    payload     = response.payload.data.decode("UTF-8")
    logging.info(f'Retreived {secret_id}')
    return payload

# Function to Request a new Access Token from Strava API
def fetch_strava_accesstoken(clientid, secret, refreshtoken):
    resp = requests.post(
        'https://www.strava.com/api/v3/oauth/token',
        params={f'client_id': {clientid}, 'client_secret': {secret}, 'grant_type': 'refresh_token', 'refresh_token': {refreshtoken}}
    )
    response = resp.json()
    logging.info(f'Retrieved refresh_token & access_token')
    return response['access_token']


# Fetch Strava Activities
def fetch_strava_activities(token):
    page, activities = 1, []
    while True:
        resp = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers={'Authorization': f'Bearer {token}'},
            params={'page': page, 'per_page': 200}
        )
        data = resp.json()
        activities += data
        if len(data) < 200:
            break
        page += 1 
        
    logging.info(f'Fetched {len(activities)} activites')
    return activities

# Activities stored in GCP BigQuery
def activites_to_bq(jsonl_lines, project, dataset, table): 
    bq_client = bigquery.Client()
    job_config = bigquery.job.LoadJobConfig()
    logging.info(f'Loading in {project} / {dataset} / {table}')
    job_config.source_format = bigquery.job.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.write_disposition = bigquery.job.WriteDisposition.WRITE_TRUNCATE # Overwrite
    job_config.create_disposition = bigquery.job.CreateDisposition.CREATE_IF_NEEDED
    job_config.autodetect = True
    job = bq_client.load_table_from_json(
        json_rows=jsonl_lines,
        destination=f'{project}.{dataset}.{table}',
        job_config=job_config
    )

    logging.info(f'Launched job id: {job.job_id}')
    return job.job_id

# Call Sequence
def run(request):
    # fetch strava values
    strava_clientid     = fetch_from_secretmanager(GCP_PROJECT_ID, STORED_CLIENT) 
    strava_clientsecret = fetch_from_secretmanager(GCP_PROJECT_ID, STORED_SECRET) 
    strava_refreshtoken = fetch_from_secretmanager(GCP_PROJECT_ID, STORED_REFRESHTOKEN) 
    # fetch new accesstoken from strava api
    strava_accesstoken  = fetch_strava_accesstoken(strava_clientid, strava_clientsecret, strava_refreshtoken)
    # fetch strava activities
    strava_activities   = fetch_strava_activities(strava_accesstoken)
    # export to BigQuery
    activites_to_bq(strava_activities, GCP_PROJECT_ID, BQ_DATASET, BQ_TABLE)
    return f"Strava API Job completed."