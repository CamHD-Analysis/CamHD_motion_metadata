


import subprocess
import logging

import json

gt_file = "classification/ground_truth.json"

with open(gt_file) as f:
    gt = json.load(f)


subprocess.run(['python', 'scripts/make_regions_proof_sheet.py',
                "--lazycache-url", "http://ursine:8080//v1/org/oceanobservatories/rawdata/files/",
                "--output", "_html/ground_truth.html"] + gt )
