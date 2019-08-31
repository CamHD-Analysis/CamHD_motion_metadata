#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path as path
import os
import random
import re
import collections
import traceback
import csv
import numpy as np

import pycamhd.region_analysis as ra

import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd

parser = argparse.ArgumentParser(description='Generate HTML proofs')

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='Regions files to process')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?', default='_summary/proof.csv', help='Output .html file')

args = parser.parse_args()

IMAGE_RESOLUTION = (426, 240) # Preserves the 16:9 aspect ratio from the original 1920x1080 images.

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig( level=args.log.upper() )

logging.info("Outfile is %s" % args.outfile)

    
REFERENCE_TAGS = {"p0_z0":9,"p0_z1":1,"p0_z2":1,
"p1_z0":2,"p1_z1":1,"p1_z2":0,
"p2_z0":2,"p2_z1":1,"p2_z2":0,
"p3_z0":2,"p3_z1":1,"p3_z2":1,
"p4_z0":2,"p4_z1":1,"p4_z2":1,
"p5_z0":2,"p5_z1":1,"p5_z2":1,
"p6_z0":2,"p6_z1":1,"p6_z2":1,
"p7_z0":2,"p7_z1":1,"p7_z2":0,
"p8_z0":2,"p8_z1":1,"p8_z2":0,
"unknown":0} 

PERCENTILES = [10, 25, 50, 75, 90]

def process( infile , writer):

    logging.info("Processing {}.".format(infile))
    
    regions = mmd.RegionFile.load(infile)

    mov = regions.mov

    tags = collections.Counter()
    inference = collections.Counter()

    probabilities = []

    for static in regions.static_regions():
        if static.unknown or not static.scene_tag or static.scene_tag == "unknown":
            tags.update(["unknown"])
        else:
            scene_tag = static.scene_tag.split('_',1)[1]
            tags.update([scene_tag])

        try:
            inference.update([static.json['sceneTagMeta']['inferredBy']])
        except Exception as e:
            logging.warning(traceback.format_exc())
            logging.warning("Unable to get inference information.")

        try:
            probabilities.append(max(static.json['sceneTagMeta']['predProbas'].values()))
        except Exception as e:
            logging.warning(traceback.format_exc())
            logging.warning("Unable to get probability information.")

    total = len(regions.regions())
    unknown = tags.get("unknown",0)
    
    error = sum(abs(REFERENCE_TAGS.get(tag,0)-tags.get(tag,0)) for tag in {**tags, **REFERENCE_TAGS})
    prob_percentiles = [(percent, np.percentile(probabilities, percent)) for percent in PERCENTILES]
    tags_sorted = [(tag, tags.get(tag, 0)) for tag in sorted({**tags, **REFERENCE_TAGS})]

    writer.writerow({
        "file" : mov,
        "total" : total,
        "unknown" : unknown,
        "error" : error,
        "percentiles" : prob_percentiles,
        "inference": inference,
        "tags" : tags_sorted,
    })


img_path  = path.dirname(args.outfile)
os.makedirs(img_path, exist_ok=True)

with open(args.outfile, 'w', newline='') as csvfile:
    fieldnames = ['file', 'total', 'unknown', 'error', 'percentiles', 'inference', 'tags']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for pathin in args.input:
        for infile in glob.iglob(pathin):

            # Iterate again
            if path.isdir(infile):
                infile = os.path.join(infile, "*_regions.json")
                for f in glob.iglob(infile):
                    process(f, writer)
            else:
                process(infile, writer)
