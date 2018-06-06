#!/usr/bin/env python3


import glob
import logging
import argparse
import os.path as path
import os
import json
import random
import math

import pycamhd.lazycache as camhd
import pycamhd.motionmetadata as mmd


parser = argparse.ArgumentParser(description='Generate HTML proofs')

parser.add_argument('input', metavar='inputfiles', nargs='+',
                    help='Regions files to include')

parser.add_argument('--scene-tag', metavar='scene_tag', nargs='?',
                    help='Scene tag to extract')

parser.add_argument('--log', metavar='log', nargs='?', default='INFO',
                    help='Logging level')

parser.add_argument('--output', dest='outdir', nargs='?', default='_timelapse/', help='Directory for timelapse images')

parser.add_argument('--image-size', dest='imgsize', nargs='?', default=None)

parser.add_argument('--lazycache-url', dest='lazycache', default=os.environ.get("LAZYCACHE_URL", "http://camhd-app-dev-nocache.appspot.com/v1/org/oceanobservatories/rawdata/files"),
                    help='URL to Lazycache repo server (only needed if classifying)')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

if not args.scene_tag:
    logging.fatal("Scene tag must be specified with --scene-tag")
    exit(-1)


qt = camhd.lazycache( args.lazycache )

img_size = None
if args.imgsize:
    img_size = args.imgsize.split('x')
    img_size = (int(img_size[0]), int(img_size[1]))


files = []

# Make a master list so we can sort on date...
for pathin in args.input:
    for infile in glob.iglob(pathin):
        # Iterate again
        if path.isdir(infile):
            infile += "*_regions.json"
            for f in glob.iglob(infile):
                files.append(mmd.RegionFile.load(f))
        else:
            files.append(mmd.RegionFile.load(infile))

logging.info("Processing %d regions files" % len(files))

files = sorted(files, key=lambda r: r.datetime())

tag = args.scene_tag

if not path.isdir(args.outdir):
    os.mkdir(args.outdir)

count = 0
for regions in files:
    r = regions.static_regions(scene_tag=tag)

    logging.info("Movie %s has %d regions tagged %s" % (regions.mov, len(r), tag))

    if len(r) == 0:
        logging.info("   This movie doesn't have any regions tagged %s, skipping" % tag)
        continue

    # Select which region
    region = r[math.floor(len(r)/2)] if len(r) > 1 else r[0]

    logging.info("Using regions from frames %d to %d" % (region.start_frame, region.end_frame))

    # Select the precise frame to retriece
    frame = region.draw()

    logging.info("Retrieving frame %d" % frame)
    img = qt.get_frame( regions.mov, frame, format='png', timeout=30 )

    if img_size:
        img.thumbnail( img_size )

    # Make filename
    filename = "%s/%08d_%s_%06d.png" % (args.outdir, count, regions.basename, frame)

    logging.info("Saving to %s" % filename)
    img.save( filename )

    count += 1



logging.info("Run \"ffmpeg -framerate 10 -pattern_type glob -i '%s/*.png' -c:v libx264 -pix_fmt yuv420p out.mp4\"" % args.outdir)
