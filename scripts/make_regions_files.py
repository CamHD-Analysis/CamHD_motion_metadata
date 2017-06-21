#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path
import subprocess


import camhd_motion_analysis as ma


parser = argparse.ArgumentParser(description='Generate _optical_flow_region.json files from _optical_flow.json files')

parser.add_argument('input', metavar='N', nargs='*',
                    help='Files or paths to process')

parser.add_argument('--dry-run', dest='dryrun', action='store_true', help='Dry run, don\'t actually process')

parser.add_argument('--force', dest='force', action='store_true', help='')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')


parser.add_argument('--git-add', dest='gitadd', action='store_true', help='Run "git add" on resulting file')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )




for path in args.input:
    for infile in glob.iglob( path, recursive=True):
        outfile = os.path.splitext(infile)[0] + "_regions.json"

        logging.info("Processing %s, Saving results to %s" % (infile, outfile) )

        if os.path.isfile( outfile ) and args.force == False:
            logging.warning("Skipping %s or run with --force to overwrite" % outfile )
            continue

        if args.dryrun == True:
            continue

        ma.region_analysis( infile, outfile=outfile )

        if os.path.isfile( outfile ) and args.gitadd:
            subprocess.run( [ "git", "add", outfile ] )
