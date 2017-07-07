#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path as path
import os
import json

import numpy as np

import region_analysis as ra


parser = argparse.ArgumentParser(description='Distill performance data from *_regions.json files')

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='Regions files to process')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?', default='performance.json', help='Output .html file')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

data = []

for pathin in args.input:
    if path.isdir(pathin):
        pathin += "**/*_optical_flow.json"

    for infile in glob.iglob( pathin, recursive=True):

        logging.info("Processing %s" % infile)

        r = ra.OpticalFlowFile( infile, flatten = False )

        if "performance" not in r.json:
            continue

        movie = r.json["movie"]
        performance = r.json["performance"]

        perFrame = [ f["durationSeconds"] for f in r.json['frameStats']]

        data.append( { "mov": r.mov,
                        "duration": movie["Duration"],
                        "numFrames": movie["NumFrames"],
                        "startTime": performance["timing"]["startTime"],
                        "endTime": performance["timing"]["endTime"],
                        "elapsedSeconds": performance["timing"]["elapsedSeconds"],
                        "cpu": performance["hostinfo"]["cpu"],
                        "perFrame": perFrame
                    })


logging.info("Processed %d files" % len(data) )

with open( args.outfile, 'w' ) as outfile:
    json.dump( data, outfile, indent=4 )
