#!/usr/bin/env python3

import glob
import logging
import argparse
import os.path as path
import os
import json

import re

import pycamhd.lazycache as camhd

from dask import compute, delayed
import dask.threaded


parser = argparse.ArgumentParser(description='Generate a movie metafile from the CI')

parser.add_argument('input', metavar='N', nargs='*',
                    help='CI paths to process')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outfile', nargs='?',
                    default='ci_scrape.json', help='Output JSON file')

parser.add_argument('--lazycache-url', dest='lazycache',
                    default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig(level=args.log.upper())

repo = camhd.lazycache(args.lazycache)

def iterate_path(path):

    if re.search('\.mov$', path):
        return [path]

    dir_info = repo.get_dir(path)

    outfiles = []

    for f in dir_info['Files']:
        if re.search('\.mov$', f):
            outfiles.append(path + f)

    for d in dir_info['Directories']:
        outfiles += iterate_path(path + d + "/")

    return outfiles

mov_paths = []
for f in args.input:
    logging.info("Iterating on %s" % f)
    mov_paths += iterate_path( f )

if len(mov_paths) == 0:
    exit


def get_metadata( mov ):
    logging.info("Retrieving %s" % mov )
    return repo.get_metadata(mov, timeout=600)


jobs = [delayed(get_metadata)(mov) for mov in mov_paths]

logging.info("Performing %d fetches" % len(jobs))

results = compute(*jobs, get=dask.threaded.get, num_workers=4)

# Convert to a map
out = {}

for res in results:
    url = res['URL']
    del res['URL']
    out[url] = res


logging.info("Processed %d paths" % len(out))

if args.outfile:
    logging.info("Saving results to %s" % args.outfile)
    with open(args.outfile, 'w') as f:
        json.dump(out, f, indent=4)
