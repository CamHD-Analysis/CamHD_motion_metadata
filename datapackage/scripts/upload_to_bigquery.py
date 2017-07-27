import io
import os
from os import path

from pprint import pprint
import json
from tabulator import Stream
from apiclient.discovery import build
from oauth2client.client import GoogleCredentials
from jsontableschema_bigquery import Storage

#from datapackage import push_datapackage

import datapackage

url="https://raw.githubusercontent.com/CamHD-Analysis/CamHD_motion_metadata/master/datapackage/datapackage.json"

package = "datapackage.json"

# Get resources
dp = datapackage.DataPackage(package)
regions = dp.resources[0]

# ## This is a little goofy
# datapath = path.dirname(package) + "/" + regions.descriptor['path']


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '.credentials.json'
credentials = GoogleCredentials.get_application_default()
service = build('bigquery', 'v2', credentials=credentials)
project = json.load(io.open('.credentials.json', encoding='utf-8'))['project_id']
dataset = 'camhd'

storage = Storage(service, project, dataset)

# Delete any existing tables
for table in reversed(storage.buckets):
    storage.delete(table)


for resource in dp.resources:
    table = resource.descriptor['name']

    # Create tables
    storage.create(table, resource.descriptor['schema'])

    storage.write(table, [d.values() for d in resource.iter()])

# List tables
print(storage.buckets)
