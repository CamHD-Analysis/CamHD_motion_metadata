import io
import os
import json
from tabulator import Stream
from apiclient.discovery import build
from oauth2client.client import GoogleCredentials
from jsontableschema_bigquery import Storage

import datapackage

# Get resources
dp = datapackage.DataPackage('../datapackage.json')
regions = dp.resources[0].data

schema = regions.schema
data = regions.data


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '.credentials.json'
credentials = GoogleCredentials.get_application_default()
service = build('bigquery', 'v2', credentials=credentials)
project = json.load(io.open('.credentials.json', encoding='utf-8'))['project_id']
dataset = 'regions'

# Storage
storage = Storage(service, project, dataset)

# Delete any existing tables
for table in reversed(storage.buckets):
    storage.delete(table)

# Create tables
storage.create('regions', schema)

# Write data to tables
storage.write('regions', data)

# List tables
print(storage.buckets)
