#!/usr/bin/env python3
#

import glob
import logging
import argparse
import os.path as path
import os
import csv

import pycamhd.motionmetadata as mmd

parser = argparse.ArgumentParser(description='Convert JSON regions files to a flat CSV format')

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='Regions files to process')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?', default='regions.csv', help='Output .csv file')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

logging.info("Outfile is %s" % args.outfile)

with open(args.outfile, 'w') as f:
    csv_file = csv.writer(f, lineterminator='\n')

    csv_file.writerow(["mov_basename","date_time","start_frame","end_frame","scene_tag"])

    def process_region_file( infile, csv_file ):
        logging.info("Processing %s" % infile)

        regions = mmd.RegionFile.load(infile)

        basename = regions.basename
        datetime = regions.datetime().isoformat()

        for r in regions.static_regions():

            csv_file.writerow( [basename, datetime, r.start_frame, r.end_frame, r.scene_tag] )

    for pathin in args.input:

        for infile in sorted(glob.iglob(pathin, recursive=True)):

            # Iterate again
            if path.isdir(infile):
                infile += "*_regions.json"
                for f in glob.iglob(infile):
                    process_region_file(f, csv_file)
            else:
                process_region_file( infile, csv_file )
