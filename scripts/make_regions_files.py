#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path as path
import os
import json

import region_analysis as ra


#import camhd_motion_analysis as ma


parser = argparse.ArgumentParser(description='Generate _optical_flow_region.json files from _optical_flow.json files')

parser.add_argument('input', metavar='N', nargs='*',
                    help='Files or paths to process')

parser.add_argument('--dry-run', dest='dryrun', action='store_true', help='Dry run, don\'t actually process')

parser.add_argument('--force', dest='force', action='store_true', help='')

parser.add_argument('--no-classify', dest='noclassify', action='store_true', help="Don't attempt to classify static regions" )

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--first', metavar='first', nargs='?', type=int,
                    help='')

parser.add_argument('--git-add', dest='gitadd', action='store_true', help='Run "git add" on resulting file')

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )



classification = {}
if not args.noclassify:
    import pycamhd.lazycache as camhd

    qt = camhd.lazycache( args.lazycache )

    if not path.exists("classification/images/"):
        logging.fatal("Need classification/images/ to perform classification.  Run scripts/fetch_classification_images.py")
        exit()

    for c in os.listdir("classification/images/"):
        if c[0] == '.':
            continue

        classification[c] = []

        for img in glob.iglob( "classification/images/%s/*.png" % c ):
            classification[c].append( path.abspath(img) )

    logging.info("Loaded classifications classes: %s " % ', '.join( classification.keys() ) )


for path in args.input:
    for infile in glob.iglob( path, recursive=True):
        outfile = os.path.splitext(infile)[0] + "_regions.json"

        logging.info("Processing %s, Saving results to %s" % (infile, outfile) )

        if os.path.isfile( outfile ) and args.force == False:
            logging.warning("Skipping %s or run with --force to overwrite" % outfile )
            continue

        if args.dryrun == True:
            continue

        with open(infile) as data_file:
            jin = json.load( data_file )

        jout = ra.region_analysis( jin )

        if not args.noclassify:
            jout = ra.classify_regions( jout, classification, lazycache = qt, first_n = args.first )

        ## Write results
        with open( outfile, 'w' ) as out:
            json.dump( jout, out, indent = 4)

        if os.path.isfile( outfile ) and args.gitadd:
            subprocess.run( [ "git", "add", outfile ] )
