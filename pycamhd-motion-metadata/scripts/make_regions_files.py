#!/usr/bin/env python3

import glob
import logging
import argparse
import os.path as path
import os
import json
import time
import subprocess

import pycamhd.region_analysis as ra

parser = argparse.ArgumentParser(description='Generate _optical_flow_region.json files from _optical_flow.json files')

parser.add_argument('input', metavar='N', nargs='*',
                    help='Files or paths to process')

parser.add_argument('--dry-run', dest='dryrun', action='store_true',
                    help='Dry run, don\'t actually process')

parser.add_argument('--force', dest='force', action='store_true', help='Remake existing files (will not overwrite ground truth files)')

parser.add_argument('--force-unclassified', dest='forceunclassified',
                    action='store_true',
                    help="Force rebuild of file only if it hasn't been classified")

parser.add_argument('--no-classify', dest='noclassify', action='store_true',
                    help="Don't attempt to classify static regions")

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--first', metavar='first', nargs='?', type=int,
                    help='')

parser.add_argument("--ground-truth", dest="groundtruth",
                    default="classification/ground_truth.json")

parser.add_argument('--git-add', dest='gitadd', action='store_true',
                    help='Run "git add" on resulting file')

parser.add_argument('--lazycache-url', dest='lazycache',
                    default=os.environ.get("LAZYCACHE_URL", None),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig(level=args.log.upper())

classifier = None
gt_library = None
qt = None
if not args.noclassify:
    import pycamhd.lazycache as camhd
    qt = camhd.lazycache(args.lazycache, verbose=True)

    gt_library = ra.GroundTruthLibrary(qt)
    gt_library.load_ground_truth(args.groundtruth)

for inpath in args.input:
    if path.isdir(inpath):
        inpath += "**/*_optical_flow.json"

    logging.info("Checking %s" % inpath)
    for infile in sorted(glob.iglob(inpath, recursive=True)):
        outfile = os.path.splitext(infile)[0] + "_regions.json"

        if os.path.isfile(outfile):

            if gt_library and outfile in gt_library.files.values():
                logging.info("%s is a ground truth file, skipping..." % outfile)
                continue
            elif args.forceunclassified and not ra.is_classified(outfile):
                logging.info("%s exists but isn't classified, overwriting" % outfile)
            elif args.force is True:
                logging.info("%s exists, overwriting" % outfile)
            else:
                logging.warning("%s exists, run with --force to overwrite" % outfile)
                continue

        ra.RegionFileMaker(first=args.first, dryrun=args.dryrun,
                          force=args.force, noclassify=args.noclassify,
                          gt_library=gt_library, lazycache=qt).make_region_file( infile, outfile )

        if os.path.isfile(outfile) and args.gitadd:
            subprocess.run(["git", "add", outfile])
