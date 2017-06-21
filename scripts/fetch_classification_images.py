#!/usr/bin/env python3

import json
import logging
import argparse
import glob

import pandas as pd
import numpy as np
import os
import os.path as path
from scipy import misc

import pycamhd.lazycache as camhd

parser = argparse.ArgumentParser(description='')

parser.add_argument('input', metavar='N', nargs='+',
                    help='*_optical_flow_regions.json file to analyze')

# parser.add_argument('--base-dir', dest='basedir', metavar='o', nargs='?',
#                     help='Base directory')

parser.add_argument('--output-dir', dest='outdir', metavar='o', nargs='?', default=".",
                    help='File for output')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--force', dest='force', action='store_true', help='Force overwrite')

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

qt = camhd.lazycache( args.lazycache )

for input_path in args.input:


    for infile in glob.iglob( input_path, recursive=True ):

        logging.info( "Processing %s" % infile)

        with open(infile) as input:
            regions_json = json.load(input)

        mov_path = regions_json['movie']['URL']

        classification_file = args.outdir + path.splitext(mov_path)[0] + "_classify.json"
        if path.exists( classification_file ):
            with open(classification_file) as f:
                classification = json.load( f )
        else:
            classification = {}

        regions = pd.DataFrame( regions_json["regions"] ).drop('stats',1)

        static = regions[ regions.type == "static"]

        min_length = 30

        static["length"] = static.endFrame - static.startFrame
        static = static.loc[ static.length >= min_length ]

        for idx,r in static.iterrows():

            logging.info("   Processing region from %d to %d" % (r.startFrame, r.endFrame) )

            samples = 5
            frames = range( r.startFrame, r.endFrame, round(r.length / (samples+1)) )
            frames = frames[1:-1]

            for f in frames:
                base_path = path.splitext(mov_path)[0] + ("/frame_%08d.png" % f)
                image_path = args.outdir + base_path
                print(image_path)

                if path.exists( image_path ) and not args.force:
                    logging.warning("Image %s already exists, not remaking" % image_path )
                    continue;

                image = qt.get_frame( mov_path, f, timeout=30 )

                os.makedirs( path.dirname(image_path), exist_ok=True )

                misc.imsave( image_path, image )

                if base_path not in classification:
                    classification[base_path] = "unknown"

        with open( classification_file, 'w') as f:
            json.dump(classification, f, indent=2)
