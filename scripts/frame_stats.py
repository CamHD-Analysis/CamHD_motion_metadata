#!/usr/bin/env python3

import argparse

from redis import Redis
from rq import Queue

import os.path
import re
import logging

import pycamhd.lazycache as pycamhd

import camhd_motion_analysis as ma

DEFAULT_STRIDE=10

parser = argparse.ArgumentParser(description='Process a file using frame_stats.')

parser.add_argument('input', metavar='N', nargs='+',
                    help='Path to process')

parser.add_argument('--threads', metavar='j', type=int, nargs='?', default=1,
                    help='Number of threads to run with dask')

parser.add_argument('--start', type=int, nargs='?', default=1,
                    help='')

parser.add_argument('--stop', metavar='j', type=int, nargs='?', default=-1,
                    help='')

parser.add_argument('--stride', metavar='s', type=int, nargs='?', default=DEFAULT_STRIDE,
                    help='Stride for frame stats')

parser.add_argument('--output-dir', dest='outdir', metavar='o', nargs='?', default="./",
                    help='File for output')

parser.add_argument('--force', dest='force', action='store_true', help='Force overwrite')

parser.add_argument('--log', metavar='log', nargs='?', default='WARNING',
                    help='Logging level')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )


#filepairs = [[f,(args.outdir + f)] for f in infiles]

infile = args.input[0]
outfile = os.path.splitext(args.outdir + infile)[0] + "_optical_flow.json"
print("Processing %s, Saving results to %s" % (infile, outfile) )

ma.process_file(infile,
                outfile,
                start=args.start,
                stop=args.stop,
                num_threads=args.threads,
                stride=args.stride )
