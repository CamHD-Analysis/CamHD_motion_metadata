#!/usr/bin/env python3

import glob
import logging
import argparse
import os.path as path
import os
import json
import time
import subprocess

import region_analysis as ra


parser = argparse.ArgumentParser(description='Generate _optical_flow_region.json files from _optical_flow.json files')

parser.add_argument('input', metavar='N', nargs='*',
                    help='Files or paths to process')

parser.add_argument('--dry-run', dest='dryrun', action='store_true',
                    help='Dry run, don\'t actually process')

parser.add_argument('--force', dest='force', action='store_true', help='')

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
                    default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig(level=args.log.upper())

classifier = None
if not args.noclassify:
    import pycamhd.lazycache as camhd
    qt = camhd.lazycache(args.lazycache)

    gt_library = ra.GroundTruthLibrary()
    gt_library.load_ground_truth(args.groundtruth)
    # classifier.load( "classification/images/" )

for inpath in args.input:
    if path.isdir( inpath ):
        inpath += "/*_optical_flow.json"

    for infile in sorted(glob.iglob(inpath, recursive=True)):
        outfile = os.path.splitext(infile)[0] + "_regions.json"

        timing = {}

        if os.path.isfile(outfile):
            if gt_library and outfile in gt_library.gt_library.keys():
                logging.info("%s is a ground truth file, skipping..." % outfile)
                continue
            elif args.forceunclassified and not ra.is_classified(outfile):
                logging.info("%s exists but isn't classified" % outfile)
            elif args.force is True:
                logging.info("%s exists, overwriting" % outfile)
            else:
                logging.warning("%s exists, run with --force to overwrite" % outfile )
                continue

        logging.info("Processing %s, Saving results to %s" % (infile, outfile))

        if args.dryrun:
            continue

        start_time = time.time()

        with open(infile) as data_file:
            jin = json.load(data_file)

        ra_start = time.time()
        jout = ra.region_analysis(jin)
        timing['regionAnalysis'] = time.time()-ra_start

        if 'versions' not in jout:
            jout['versions'] = {}
        jout['versions']['findRegions'] = ra.find_regions_version
        jout['performance'] = {'timing': timing}

        if 'depends' not in jout:
            jout['depends'] = {}

        git_rev = ra.git_revision(infile)
        jout['depends'] = {'opticalFlow': {infile: git_rev}}

        # Write results as a checkpoint
        with open(outfile, 'w') as out:
            json.dump(jout, out, indent=4)

        url = jout["movie"]["URL"]

        if not args.noclassify:
            classifier_start = time.time()

            classifier = gt_library.select(url)

            jout = ra.classify_regions(jout, classifier, lazycache=qt,
                                       first_n=args.first)
            timing['classification'] = time.time()-classifier_start

            if 'versions' not in jout:
                jout['versions'] = {}
            jout['versions']['classifyRegions'] = ra.classify_regions_version

        timing['elapsedSeconds'] = time.time()-start_time

        jout['performance'] = {'timing': timing}

        # Write results
        with open(outfile, 'w') as out:
            json.dump(jout, out, indent=4)

        if os.path.isfile(outfile) and args.gitadd:
            subprocess.run(["git", "add", outfile])
