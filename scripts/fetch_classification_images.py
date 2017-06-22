#!/usr/bin/env python3

import json
import logging
import argparse
import glob

import requests

import pandas as pd
import numpy as np
import os
import os.path as path
from scipy import misc

import pycamhd.lazycache as camhd

parser = argparse.ArgumentParser(description='')

parser.add_argument('input', metavar='N', nargs='*',
                    help='*_optical_flow_regions.json to analyze')

# parser.add_argument('--base-dir', dest='basedir', metavar='o', nargs='?',
#                     help='Base directory')

parser.add_argument("--ground-truth", dest='groundtruth', nargs='*',
                    default=['classification/ground_truth/*.json'],
                    help='Ground truth files to load')

parser.add_argument("--regions-root", dest='regionsroot', nargs='?',
                    default='.',
                    help='Location of regions files')

parser.add_argument('--output-dir', dest='outdir', metavar='o', nargs='?', default="classification/images/",
                    help='File for output')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--force', dest='force', action='store_true', help='Force overwrite of images')

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

qt = camhd.lazycache( args.lazycache )


regions={}
ground_truth={}

## Any regions files specified on the command line should be added to regions
for input_path in args.input:
    # Process command line arg if it's a glob
    for infile in glob.iglob( input_path, recursive=True ):

        logging.info( "Adding regions file %s" % infile)

        with open(infile) as input:
            regions_json = json.load(input)

        if "regions" in regions_json.keys():
            regions[ regions_json["movie"]["URL"] ] = regions_json["regions"]

## Load dict keys
for gt_path in args.groundtruth:
    for infile in glob.iglob( gt_path, recursive=True ):

        logging.info( "Adding ground truth file %s" % infile)

        with open(infile) as input:
            gt_json = json.load(input)

        ground_truth.update( gt_json )

# For any keys in ground truth but not in regions, open regions file
for key in ground_truth.keys():
    if key in regions.keys():
        continue

    logging.info("Loading regions file for %s", key)

    region_file = args.regionsroot + key.replace('.mov', '_optical_flow_regions.json')

    logging.info("Loading region file %s" % region_file )

    if path.exists( region_file ) == False:
        logging.fatal("Couldn't find region file %s" % region_file )
        exit()

    with open(region_file) as input:
        regions_json = json.load(input)

    regions[ regions_json["movie"]["URL"] ] = regions_json["regions"]


print( regions.keys() )
print( ground_truth.keys() )

if regions.keys() != ground_truth.keys():
    logging.fatal("Unexpected key mismatch")
    exit()

for k,gt in ground_truth.items():

    logging.info("Examining %s" % k )

    for frame, c in gt.items():
        frame = int(frame)
        logging.info("Getting frame %d of class %s", frame, c )

        bname = path.splitext( path.basename( k ))[0]
        outfile = "%s/%s/%s_%08d.png" % (args.outdir, c, bname, frame)

        print(outfile)
        if path.exists(outfile) and not args.force:
            logging.info("Image %s exists, skipping" % outfile)
            continue

        img = qt.get_frame( k, frame, timeout = 30, format='png' )

        # if img.shape != (1080,1920,3):
        #      logging.warning("Something went wrong with getting the image (shape %s)" % str(img.shape) )
        #      continue

        os.makedirs( path.dirname( outfile ), exist_ok=True )
        with open( outfile,'wb' ) as f:
            img.save(f)


        #
        # mov_path = regions_json['movie']['URL']
        #
        # classification_file = args.outdir + path.splitext(mov_path)[0] + "_classify.json"
        # if path.exists( classification_file ):
        #     with open(classification_file) as f:
        #         classification = json.load( f )
        # else:
        #     classification = {}
        #
        # regions = pd.DataFrame( regions_json["regions"] ).drop('stats',1)
        #
        # static = regions[ regions.type == "static"]
        #
        # min_length = 30
        #
        # static["length"] = static.endFrame - static.startFrame
        # static = static.loc[ static.length >= min_length ]
        #
        # for idx,r in static.iterrows():
        #
        #     logging.info("   Processing region from %d to %d" % (r.startFrame, r.endFrame) )
        #
        #     samples = 5
        #     frames = range( r.startFrame, r.endFrame, round(r.length / (samples+1)) )
        #     frames = frames[1:-1]
        #
        #     for f in frames:
        #         base_path = path.splitext(mov_path)[0] + ("/frame_%08d.png" % f)
        #         image_path = args.outdir + base_path
        #         print(image_path)
        #
        #         if path.exists( image_path ) and not args.force:
        #             logging.warning("Image %s already exists, not remaking" % image_path )
        #             continue;
        #
        #         image = qt.get_frame( mov_path, f, timeout=30 )
        #
        #         os.makedirs( path.dirname(image_path), exist_ok=True )
        #
        #         misc.imsave( image_path, image )
        #
        #         if base_path not in classification:
        #             classification[base_path] = "unknown"
        #
        # with open( classification_file, 'w') as f:
        #     json.dump(classification, f, indent=2)
